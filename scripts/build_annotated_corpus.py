"""
Gera corpus anotado inicial a partir de documentos reais coletados.

Uso:
python3 scripts/build_annotated_corpus.py --size 30 --output data/corpus/annotated_corpus.jsonl
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agents.analysis_agent import AnalysisAgent
from src.agents.monitor_agent import MonitorAgent


def build_corpus(size: int) -> list[dict]:
    monitor = MonitorAgent()
    analysis_agent = AnalysisAgent()

    collected = monitor.monitor_sources()
    unique_docs = monitor.eliminate_duplicates(collected)
    screened_docs = monitor.initial_screening(unique_docs)
    selected = screened_docs[: max(1, size)]

    corpus_entries = []
    for doc in selected:
        metadata = {
            "id": doc.id,
            "title": doc.title,
            "source": doc.source,
            "document_type": doc.document_type,
            "url": doc.url,
            "published_date": doc.published_date,
        }
        analysis = asdict(analysis_agent.analyze_document(doc.content, metadata))
        corpus_entries.append(
            {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "document_type": doc.document_type,
                "url": doc.url,
                "published_date": doc.published_date.isoformat(),
                "content": doc.content,
                "annotation_status": "seeded_auto_needs_human_review",
                "gold": {
                    "relevance": bool(analysis.get("impact_score", 0.0) >= 0.5),
                    "effective_date": analysis.get("effective_date").isoformat() if analysis.get("effective_date") else None,
                    "implementation_deadline": (
                        analysis.get("implementation_deadline").isoformat()
                        if analysis.get("implementation_deadline")
                        else None
                    ),
                    "obligations": analysis.get("obligations", []),
                    "affected_activities": analysis.get("affected_activities", []),
                    "impact_score": analysis.get("impact_score", 0.0),
                },
            }
        )
    return corpus_entries


def main():
    parser = argparse.ArgumentParser(description="Geração de corpus anotado inicial")
    parser.add_argument("--size", type=int, default=30, help="Quantidade de documentos no corpus (30-50 recomendado).")
    parser.add_argument(
        "--output",
        type=str,
        default="data/corpus/annotated_corpus.jsonl",
        help="Arquivo de saída JSONL.",
    )
    args = parser.parse_args()

    entries = build_corpus(args.size)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Corpus gerado com {len(entries)} documentos em {output_path}")


if __name__ == "__main__":
    main()
