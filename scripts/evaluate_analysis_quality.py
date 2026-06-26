"""
Avala qualidade da análise contra corpus anotado.

Uso:
python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --models llama3.2:3b,deepseek-r1:8b
python3 scripts/evaluate_analysis_quality.py --corpus data/corpus/annotated_corpus.jsonl --heuristic-only
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import requests
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from src.agents.analysis_agent import AnalysisAgent
from src.utils.evaluation import evaluate_corpus_predictions
from src.utils.llm_integration import RegulatoryLLM, RegulatoryLLMConfig


def load_corpus(path: str) -> list[dict]:
    entries = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def _parse_published_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def run_predictions_heuristic(corpus: list[dict]) -> dict[str, dict]:
    agent = AnalysisAgent()
    predictions: dict[str, dict] = {}
    for item in corpus:
        metadata = {
            "id": item["id"],
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "document_type": item.get("document_type", ""),
            "url": item.get("url", ""),
            "published_date": _parse_published_date(item.get("published_date")),
        }
        result = asdict(agent.analyze_document(item.get("content", ""), metadata))
        predictions[item["id"]] = result
    return predictions


def _check_health(base_url: str) -> Optional[str]:
    health_url = f"{base_url.rstrip('/')}/health"
    try:
        response = requests.get(health_url, timeout=20)
        response.raise_for_status()
        return None
    except requests.RequestException as exc:
        return f"health check falhou: {exc}"


def run_predictions_llm(
    corpus: list[dict],
    model_name: str,
    llm_timeout_seconds: int,
    llm_max_tokens: int,
    llm_retries: int,
) -> tuple[dict[str, dict], dict]:
    config = RegulatoryLLMConfig.from_env()
    if not config:
        raise RuntimeError("LLM não configurado no ambiente para avaliação por modelo.")

    health_warning = _check_health(config.base_url)
    config.model = model_name
    config.timeout_seconds = llm_timeout_seconds
    config.max_tokens = llm_max_tokens
    config.max_retries = llm_retries
    llm = RegulatoryLLM(config)
    agent = AnalysisAgent(llm_model=llm)

    predictions: dict[str, dict] = {}
    llm_ok = 0
    fallback_count = 0
    for item in corpus:
        metadata = {
            "id": item["id"],
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "document_type": item.get("document_type", ""),
            "url": item.get("url", ""),
            "published_date": _parse_published_date(item.get("published_date")),
        }
        result = asdict(agent.analyze_document(item.get("content", ""), metadata))
        if result.get("extraction_method") == "llm":
            llm_ok += 1
        else:
            fallback_count += 1
        predictions[item["id"]] = result
    telemetry = {
        "documents_evaluated": len(corpus),
        "llm_success_count": llm_ok,
        "fallback_count": fallback_count,
    }
    if health_warning:
        telemetry["health_warning"] = health_warning
    return predictions, telemetry


def main():
    if load_dotenv:
        # Garante que scripts executados via CLI também leiam o .env do projeto.
        load_dotenv(ROOT_DIR / ".env")

    parser = argparse.ArgumentParser(description="Avaliação de qualidade da análise regulatória")
    parser.add_argument("--corpus", required=True, help="Caminho do corpus anotado (.jsonl)")
    parser.add_argument("--heuristic-only", action="store_true", help="Avalia apenas baseline heurístico")
    parser.add_argument(
        "--models",
        default="llama3.2:3b,deepseek-r1:8b",
        help="Lista de modelos separada por vírgula para comparar (quando LLM estiver configurado).",
    )
    parser.add_argument(
        "--report-output",
        default="reports/quality",
        help="Diretório de saída do relatório consolidado.",
    )
    parser.add_argument(
        "--comparison-samples",
        type=int,
        default=8,
        help="Quantidade de documentos para comparação entre modelos (evita timeout em lote grande).",
    )
    parser.add_argument("--llm-timeout", type=int, default=45, help="Timeout por chamada de avaliação LLM.")
    parser.add_argument("--llm-max-tokens", type=int, default=400, help="Máximo de tokens por chamada na avaliação.")
    parser.add_argument("--llm-retries", type=int, default=1, help="Retries por chamada durante a avaliação.")
    args = parser.parse_args()

    corpus = load_corpus(args.corpus)
    if not corpus:
        raise RuntimeError("Corpus vazio.")

    evaluations = {}

    heuristic_predictions = run_predictions_heuristic(corpus)
    evaluations["heuristic"] = evaluate_corpus_predictions(corpus, heuristic_predictions)

    if not args.heuristic_only:
        model_names = [name.strip() for name in args.models.split(",") if name.strip()]
        comparison_corpus = corpus[: max(1, args.comparison_samples)]
        for model_name in model_names:
            try:
                predictions, telemetry = run_predictions_llm(
                    comparison_corpus,
                    model_name=model_name,
                    llm_timeout_seconds=args.llm_timeout,
                    llm_max_tokens=args.llm_max_tokens,
                    llm_retries=args.llm_retries,
                )
                evaluations[f"llm:{model_name}"] = {
                    **evaluate_corpus_predictions(comparison_corpus, predictions),
                    "telemetry": telemetry,
                }
            except Exception as exc:
                evaluations[f"llm:{model_name}"] = {"error": str(exc)}

    report = {
        "generated_at": datetime.now().isoformat(),
        "corpus_path": os.path.abspath(args.corpus),
        "sample_size": len(corpus),
        "results": evaluations,
    }

    output_dir = Path(args.report_output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Relatório salvo em: {output_path}")


if __name__ == "__main__":
    main()
