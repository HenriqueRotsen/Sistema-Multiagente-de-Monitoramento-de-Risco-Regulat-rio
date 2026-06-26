"""
Cliente LLM configuravel para analise regulatoria.

Suporta:
- Ollama/proxy da disciplina: POST /api/chat com header X-API-Key
- OpenAI-compatible: POST /chat/completions com bearer token opcional
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class RegulatoryLLMConfig:
    """Configuracao minima para chamadas LLM."""
    base_url: str
    model: str
    provider: str = "ollama"
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    timeout_seconds: int = 60
    temperature: float = 0.1
    max_tokens: int = 1200
    max_retries: int = 2
    retry_backoff_seconds: float = 1.0
    rate_limit_per_minute: int = 20

    @classmethod
    def from_env(cls) -> Optional["RegulatoryLLMConfig"]:
        """Cria configuracao a partir de variaveis de ambiente."""
        base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
        model = os.getenv("LLM_MODEL", "").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip() or None
        provider = os.getenv("LLM_PROVIDER", "").strip().lower()

        if api_key in {"your_api_key_here", "none", "null", "-"}:
            api_key = None

        if not base_url or not model:
            return None

        if not provider:
            provider = "ollama" if "ollama" in base_url.lower() else "openai"

        return cls(
            base_url=base_url,
            model=model,
            provider=provider,
            api_key=api_key,
            api_key_header=os.getenv("LLM_API_KEY_HEADER", "X-API-Key"),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1200")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
            retry_backoff_seconds=float(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "1.0")),
            rate_limit_per_minute=int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "20")),
        )


class RegulatoryLLM:
    """Wrapper pequeno para extracao estruturada com LLM."""

    def __init__(self, config: RegulatoryLLMConfig):
        self.config = config
        self._last_request_ts: Optional[float] = None

    @classmethod
    def from_env(cls) -> Optional["RegulatoryLLM"]:
        """Retorna cliente configurado ou None se faltarem variaveis."""
        config = RegulatoryLLMConfig.from_env()
        if not config:
            return None
        return cls(config)

    def analyze_regulation(self, text: str, metadata: Dict[str, Any], sector_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa documento regulatorio e retorna JSON normalizado.

        O prompt pede apenas fatos rastreaveis no texto; inferencias devem ser
        marcadas com baixa/media confianca pelo modelo.
        """
        prompt = self._build_prompt(text, metadata, sector_profile)
        raw_response = self._chat_completion(prompt)
        parsed = self._parse_json_object(raw_response)
        return self._normalize_response(parsed)

    def _chat_completion(self, prompt: str) -> str:
        if self.config.provider == "ollama":
            return self._ollama_chat(prompt)
        if self.config.provider == "openai":
            return self._openai_compatible_chat(prompt)
        raise ValueError(f"Provedor LLM não suportado: {self.config.provider}")

    def _ollama_chat(self, prompt: str) -> str:
        url = f"{self.config.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers[self.config.api_key_header] = self.config.api_key

        payload = {
            "model": self.config.model,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em regulacao financeira brasileira. "
                        "Extraia informacoes com conservadorismo, sem inventar dados ausentes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        data = self._post_json_with_retry(url, headers, payload, provider_name="ollama")
        if "error" in data:
            raise RuntimeError(f"Ollama erro: {data['error']}")
        return data["message"]["content"]

    def _openai_compatible_chat(self, prompt: str) -> str:
        url = f"{self.config.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em regulacao financeira brasileira. "
                        "Extraia informacoes com conservadorismo, sem inventar dados ausentes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        data = self._post_json_with_retry(url, headers, payload, provider_name="openai")
        return data["choices"][0]["message"]["content"]

    def _post_json_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        provider_name: str,
    ) -> Dict[str, Any]:
        retries = max(0, self.config.max_retries)
        last_exception: Optional[Exception] = None

        for attempt in range(retries + 1):
            self._wait_for_rate_limit_slot()
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_exception = exc
                if attempt >= retries:
                    break
                backoff = self.config.retry_backoff_seconds * (2 ** attempt)
                logger.warning(
                    "Falha em chamada %s (tentativa %s/%s). Retry em %.1fs: %s",
                    provider_name,
                    attempt + 1,
                    retries + 1,
                    backoff,
                    str(exc),
                )
                time.sleep(backoff)

        raise RuntimeError(f"Falha ao chamar provedor {provider_name}: {last_exception}")

    def _wait_for_rate_limit_slot(self):
        """Rate limiting simples por intervalo mínimo entre chamadas."""
        rpm = max(1, self.config.rate_limit_per_minute)
        min_interval_seconds = 60.0 / float(rpm)
        now = time.monotonic()
        if self._last_request_ts is not None:
            elapsed = now - self._last_request_ts
            if elapsed < min_interval_seconds:
                time.sleep(min_interval_seconds - elapsed)
        self._last_request_ts = time.monotonic()

    def _build_prompt(self, text: str, metadata: Dict[str, Any], sector_profile: Dict[str, Any]) -> str:
        clipped_text = text[:12000]
        sector = sector_profile.get("name", "Fintechs e Instituicoes de Pagamento")
        activities = ", ".join(sector_profile.get("activities", []))
        risk_areas = ", ".join(sector_profile.get("risk_areas", []))

        return f"""
Analise o documento regulatorio abaixo para o setor: {sector}.

Metadados:
- Titulo: {metadata.get("title", "")}
- Regulador: {metadata.get("source", "")}
- Tipo: {metadata.get("document_type", "")}
- Fonte: {metadata.get("url", "")}

Atividades monitoradas: {activities}
Areas de risco esperadas: {risk_areas}

Retorne SOMENTE um JSON valido com estas chaves:
{{
  "summary": "resumo objetivo em portugues, ate 120 palavras",
  "effective_date": "YYYY-MM-DD ou null",
  "implementation_deadline": "YYYY-MM-DD ou null",
  "affected_activities": ["lista curta"],
  "affected_entities": ["lista curta"],
  "obligations": ["obrigacoes concretas, se houver"],
  "recommendations": ["acoes iniciais recomendadas para triagem humana"],
  "keywords": ["ate 8 termos"],
  "impact_score": 0.0,
  "impact_description": "avaliacao curta de impacto para o setor",
  "impact_areas": ["Compliance", "Tecnologia", "Operacional", "Juridico", "Produtos", "Risco"],
  "confidence_scores": {{
    "summary": 0.0,
    "dates": 0.0,
    "obligations": 0.0,
    "impact": 0.0
  }}
}}

Regras:
- Use null quando uma data ou prazo nao estiver explicito.
- Nao transforme recomendacoes gerais em obrigacoes.
- Recomende acoes de triagem, nao aconselhamento juridico definitivo.
- Se o documento for apenas noticia sobre evento ou pesquisa, deixe "obligations" vazio e reduza "impact_score".
- "impact_score" deve ficar entre 0 e 1.

Documento:
\"\"\"
{clipped_text}
\"\"\"
""".strip()

    def _parse_json_object(self, raw_response: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_response, flags=re.DOTALL)
            if not match:
                raise ValueError("Resposta do LLM nao contem JSON valido")
            return json.loads(match.group(0))

    def _normalize_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Garante formato previsivel mesmo quando o modelo varia levemente."""
        return {
            "summary": str(data.get("summary") or ""),
            "effective_date": data.get("effective_date"),
            "implementation_deadline": data.get("implementation_deadline"),
            "affected_activities": self._list_of_strings(data.get("affected_activities")),
            "affected_entities": self._list_of_strings(data.get("affected_entities")),
            "obligations": self._list_of_strings(data.get("obligations")),
            "recommendations": self._list_of_strings(data.get("recommendations")),
            "keywords": self._list_of_strings(data.get("keywords"))[:8],
            "impact_score": self._float_between_zero_and_one(data.get("impact_score"), default=0.3),
            "impact_description": str(data.get("impact_description") or ""),
            "impact_areas": self._list_of_strings(data.get("impact_areas")),
            "confidence_scores": self._confidence_scores(data.get("confidence_scores")),
        }

    def _list_of_strings(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def _float_between_zero_and_one(self, value: Any, default: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default

    def _confidence_scores(self, value: Any) -> Dict[str, float]:
        if not isinstance(value, dict):
            return {"summary": 0.0, "dates": 0.0, "obligations": 0.0, "impact": 0.0}
        return {
            key: self._float_between_zero_and_one(value.get(key), default=0.0)
            for key in ("summary", "dates", "obligations", "impact")
        }
