"""
Analysis Agent - Analisa impacto regulatório e extrai informações estruturadas
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInfo:
    """Informações extraídas de um documento regulatório"""
    document_id: str
    regulatory_body: str  # BCB, CVM
    document_type: str
    title: str
    summary: str = ""
    
    # Informações estruturadas extraídas
    effective_date: Optional[datetime] = None
    implementation_deadline: Optional[datetime] = None
    affected_activities: List[str] = field(default_factory=list)
    affected_entities: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Estimativa de impacto
    impact_score: float = 0.0  # 0.0 (baixo) a 1.0 (alto)
    impact_description: str = ""
    impact_areas: List[str] = field(default_factory=list)  # Compliance, Tecnologia, Operacional, etc
    
    # Confiança das extrações
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    extraction_method: str = "heuristic"  # "llm" ou "regex"


class AnalysisAgent:
    """
    Agente responsável por:
    1. Análise profunda de conteúdo regulatório
    2. Extração de informações estruturadas
    3. Estimativa de impacto
    4. Identificação de entidades afetadas
    """

    def __init__(self, llm_model=None, embedding_model=None):
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.sector_profile = {
            "name": "Fintechs e Instituições de Pagamento",
            "keywords": self._get_sector_keywords(),
            "activities": self._get_affected_activities(),
            "risk_areas": ["Compliance", "Segurança", "PLD/FT", "Open Banking", "Autenticação"]
        }

    def analyze_document(self, document_text: str, metadata: Dict[str, Any]) -> ExtractedInfo:
        """
        Analisa um documento completo e extrai informações estruturadas
        """
        logger.info(f"Analisando documento: {metadata.get('title', 'sem título')}")
        
        info = ExtractedInfo(
            document_id=metadata.get('id', ''),
            regulatory_body=metadata.get('source', ''),
            document_type=metadata.get('document_type', ''),
            title=metadata.get('title', '')
        )

        if self.llm_model:
            try:
                self._apply_llm_analysis(document_text, metadata, info)
                return info
            except Exception as e:
                logger.error("Erro ao analisar com LLM; usando fallback heurístico: %s", str(e))
        
        # Executa pipeline de extração
        self._extract_summary(document_text, info)
        self._extract_dates(document_text, info, metadata)
        self._extract_obligations(document_text, info)
        self._extract_affected_entities(document_text, info)
        self._extract_keywords(document_text, info)
        self._estimate_impact(document_text, info)
        self._generate_recommendations(info)
        
        return info

    def _apply_llm_analysis(self, text: str, metadata: Dict[str, Any], info: ExtractedInfo):
        """Preenche ExtractedInfo a partir de resposta estruturada do LLM."""
        result = self.llm_model.analyze_regulation(text, metadata, self.sector_profile)

        info.summary = result.get("summary", "")
        info.effective_date = self._parse_iso_date(result.get("effective_date"))
        info.implementation_deadline = self._parse_iso_date(result.get("implementation_deadline"))
        info.affected_activities = result.get("affected_activities", [])
        info.affected_entities = result.get("affected_entities", [])
        info.obligations = result.get("obligations", [])
        info.keywords = result.get("keywords", [])
        info.recommendations = result.get("recommendations", [])
        info.impact_score = result.get("impact_score", 0.0)
        info.impact_description = result.get("impact_description", "")
        info.impact_areas = result.get("impact_areas", [])
        info.confidence_scores = result.get("confidence_scores", {})
        info.extraction_method = "llm"

    def _extract_summary(self, text: str, info: ExtractedInfo):
        """
        Sumarização simples para fallback sem LLM.
        """
        clean_text = " ".join(text.split())
        info.summary = clean_text[:500] + ("..." if len(clean_text) > 500 else "")
        info.confidence_scores['summary'] = 0.45 if info.summary else 0.0

    def _extract_dates(self, text: str, info: ExtractedInfo, metadata: Dict[str, Any]):
        """
        Extração heurística de datas explícitas.
        """
        effective_date, deadline = self._find_contextual_dates(
            text,
            reference_date=metadata.get("published_date"),
        )
        info.effective_date = effective_date
        info.implementation_deadline = deadline

        if effective_date or deadline:
            info.confidence_scores['dates'] = 0.55
        else:
            info.confidence_scores['dates'] = 0.0

    def _extract_obligations(self, text: str, info: ExtractedInfo):
        """
        Extração heurística de obrigações por padrões modais.
        """
        obligation_patterns = [
            r"\bdever[aã]o?\b",
            r"\bdevem\b",
            r"\bdeve\b",
            r"\bficam?\s+(?:obrigad[oa]s?|determinad[oa]s?)\b",
            r"\bé\s+obrigat[oó]ri[oa]\b",
            r"\bser[aã]\s+obrigat[oó]ri[oa]\b",
            r"\bter[aã]o?\s+que\b",
        ]
        sentences = self._split_sentences(text)
        obligations = []
        for sentence in sentences:
            sentence_clean = " ".join(sentence.split())
            if any(re.search(pattern, sentence_clean, flags=re.IGNORECASE) for pattern in obligation_patterns):
                obligations.append(sentence_clean[:350])

        info.obligations = obligations[:8]
        info.confidence_scores['obligations'] = 0.55 if info.obligations else 0.0

    def _extract_affected_entities(self, text: str, info: ExtractedInfo):
        """
        Extração simples de entidades setoriais afetadas.
        """
        info.affected_activities = self._match_sector_keywords(text)
        entity_patterns = [
            "instituições financeiras",
            "instituições de pagamento",
            "fintechs",
            "participantes do Pix",
            "iniciadores de transação de pagamento",
            "conglomerado prudencial",
            "corretoras",
            "distribuidoras",
        ]
        text_lower = text.lower()
        info.affected_entities = [
            entity for entity in entity_patterns if entity in text_lower
        ]
        info.confidence_scores['entities'] = 0.5 if info.affected_entities or info.affected_activities else 0.0

    def _extract_keywords(self, text: str, info: ExtractedInfo):
        """
        Keywords por interseção com perfil setorial.
        """
        text_lower = text.lower()
        info.keywords = [
            keyword
            for keyword in self.sector_profile['keywords']
            if keyword in text_lower
        ][:8]
        info.confidence_scores['keywords'] = 0.5 if info.keywords else 0.0

    def _estimate_impact(self, text: str, info: ExtractedInfo):
        """
        Estimativa heurística de impacto.
        """
        text_lower = text.lower()
        sector_matches = sum(1 for kw in self.sector_profile['keywords'] if kw in text_lower)
        obligation_weight = 0.2 if info.obligations else 0.0
        deadline_weight = 0.1 if info.implementation_deadline else 0.0
        info.impact_score = min(1.0, 0.2 + (sector_matches * 0.08) + obligation_weight + deadline_weight)
        info.impact_areas = self._infer_impact_areas(text_lower)
        info.impact_description = (
            "Impacto estimado por heurística local; revisar com especialista."
            if info.impact_score >= 0.5
            else "Baixo impacto setorial estimado por heurística local."
        )
        info.confidence_scores['impact'] = 0.45
        info.extraction_method = "regex"

    def _generate_recommendations(self, info: ExtractedInfo):
        """Gera recomendações de fallback quando não há LLM."""
        recommendations = []
        if info.obligations:
            recommendations.append("Encaminhar obrigações extraídas para revisão de compliance.")
        if info.implementation_deadline:
            recommendations.append("Registrar prazo no calendário regulatório e definir responsável interno.")
        if any(area in info.impact_areas for area in ["Tecnologia", "Segurança"]):
            recommendations.append("Acionar times de tecnologia e segurança para avaliação de impacto.")
        if not recommendations:
            recommendations.append("Revisar documento com especialista antes de qualquer ação.")

        info.recommendations = recommendations

    def _match_sector_keywords(self, text: str) -> List[str]:
        """Identifica atividades afetadas baseado em keywords"""
        matched = []
        text_lower = text.lower()
        
        for activity in self.sector_profile['activities']:
            if activity.lower() in text_lower:
                matched.append(activity)
        
        return matched

    def _get_sector_keywords(self) -> List[str]:
        """Keywords relevantes para fintechs e pagamentos"""
        return [
            "pagamento", "fintech", "cartão", "transferência", "instituição de pagamento",
            "gateway", "wallet", "criptomoeda", "open banking", "pix", "autenticação",
            "segurança", "pld", "fraude", "compliance", "capital", "prudencial"
        ]

    def _get_affected_activities(self) -> List[str]:
        """Atividades que podem ser afetadas"""
        return [
            "Processamento de pagamentos",
            "Transferências interbancárias",
            "Carteiras digitais",
            "Custódia de criptoativos",
            "Crédito ao consumidor",
            "Open Banking",
            "Autenticação e segurança",
            "Conformidade com regulações",
            "Relatórios regulatórios"
        ]

    def _parse_iso_date(self, value: Any) -> Optional[datetime]:
        """Converte YYYY-MM-DD vindo do LLM para datetime."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _find_dates(self, text: str) -> List[datetime]:
        """Localiza datas em formatos brasileiros comuns."""
        dates = []
        patterns = [
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
            r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b",
            r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                parts = [int(part) for part in match.groups()]
                try:
                    if pattern.startswith(r"\b(\d{4})"):
                        dates.append(datetime(parts[0], parts[1], parts[2]))
                    else:
                        dates.append(datetime(parts[2], parts[1], parts[0]))
                except ValueError:
                    continue
        return sorted(set(dates))

    def _find_contextual_dates(
        self,
        text: str,
        reference_date: Optional[datetime] = None,
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """Extrai datas apenas quando há contexto de prazo ou vigência."""
        effective_date = None
        deadline = None

        for sentence in self._split_sentences(text):
            dates = self._find_dates(sentence)
            if not dates:
                continue
            if reference_date:
                dates = [date for date in dates if date.date() >= reference_date.date()]
                if not dates:
                    continue

            sentence_lower = sentence.lower()
            if re.search(r"\b(vig[êe]ncia|entra em vigor|a partir de|passa a valer)\b", sentence_lower):
                effective_date = effective_date or dates[0]

            if re.search(r"\b(prazo|deadline|até|ate|dever[aã]o?|devem|obrigat[oó]ri[oa])\b", sentence_lower):
                deadline = deadline or dates[-1]

        return effective_date, deadline

    def _split_sentences(self, text: str) -> List[str]:
        """Divide texto em sentenças suficientes para extração simples."""
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]

    def _infer_impact_areas(self, text_lower: str) -> List[str]:
        """Infere áreas impactadas a partir de palavras-chave."""
        areas = []
        mappings = {
            "Compliance": ["compliance", "conformidade", "regula", "norma", "obrig"],
            "Tecnologia": ["api", "open finance", "open banking", "pix", "sistema", "tecnologia"],
            "Segurança": ["segurança", "fraude", "autenticação", "identidade"],
            "PLD/FT": ["pld", "lavagem", "terrorismo"],
            "Operacional": ["prazo", "processo", "procedimento", "relatório"],
        }
        for area, keywords in mappings.items():
            if any(keyword in text_lower for keyword in keywords):
                areas.append(area)
        return areas or ["Compliance"]

    def batch_analyze(self, documents: List[Dict[str, Any]]) -> List[ExtractedInfo]:
        """Analisa lote de documentos"""
        results = []
        
        for doc in documents:
            try:
                info = self.analyze_document(
                    doc.get('content', ''),
                    doc.get('metadata', {})
                )
                results.append(info)
            except Exception as e:
                logger.error(f"Erro ao analisar documento {doc.get('id')}: {str(e)}")
        
        return results

    def filter_by_relevance(self, analyses: List[ExtractedInfo], threshold: float = 0.5) -> List[ExtractedInfo]:
        """Filtra análises por score de impacto"""
        return [a for a in analyses if a.impact_score >= threshold]
