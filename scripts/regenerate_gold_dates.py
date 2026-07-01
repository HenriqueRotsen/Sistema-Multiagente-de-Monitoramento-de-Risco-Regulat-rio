"""
Regenera apenas as datas gold (effective_date / implementation_deadline) de um
corpus anotado já existente, sem recoletar documentos novos do BCB/CVM.

Motivação: a extração heurística de datas em `AnalysisAgent._find_dates` não
reconhecia datas por extenso em português (ex.: "17 de junho", "1º de outubro"),
formato dominante nos textos reais do BCB/CVM. Como o corpus gold foi semeado
rodando essa mesma extração heurística, todas as entradas ficaram com
effective_date/implementation_deadline = None, tornando a métrica
`date_accuracy` estruturalmente 0/0 (relatada como 0.0) em todos os relatórios
de qualidade anteriores. Este script reaplica a extração (já corrigida) sobre
o `content` existente de cada documento, mantendo a amostra de 30 documentos
e os demais campos gold (relevance, obligations, impact_score) intactos.

Uso:
python3 scripts/regenerate_gold_dates.py --corpus data/corpus/annotated_corpus.jsonl
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agents.analysis_agent import AnalysisAgent


def regenerate(corpus_path: Path) -> list[dict]:
    analysis_agent = AnalysisAgent()
    entries = []
    with corpus_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    before_effective = sum(1 for e in entries if e.get("gold", {}).get("effective_date"))
    before_deadline = sum(1 for e in entries if e.get("gold", {}).get("implementation_deadline"))

    for entry in entries:
        published_date = None
        if entry.get("published_date"):
            published_date = datetime.fromisoformat(entry["published_date"])

        metadata = {
            "id": entry["id"],
            "title": entry["title"],
            "source": entry["source"],
            "document_type": entry["document_type"],
            "url": entry.get("url"),
            "published_date": published_date,
        }
        analysis = analysis_agent.analyze_document(entry["content"], metadata)
        entry["gold"]["effective_date"] = (
            analysis.effective_date.isoformat() if analysis.effective_date else None
        )
        entry["gold"]["implementation_deadline"] = (
            analysis.implementation_deadline.isoformat()
            if analysis.implementation_deadline
            else None
        )

    after_effective = sum(1 for e in entries if e.get("gold", {}).get("effective_date"))
    after_deadline = sum(1 for e in entries if e.get("gold", {}).get("implementation_deadline"))

    print(f"effective_date não-nulo: {before_effective}/{len(entries)} -> {after_effective}/{len(entries)}")
    print(f"implementation_deadline não-nulo: {before_deadline}/{len(entries)} -> {after_deadline}/{len(entries)}")

    return entries


def main():
    parser = argparse.ArgumentParser(description="Regenera datas gold de um corpus existente")
    parser.add_argument(
        "--corpus",
        type=str,
        default="data/corpus/annotated_corpus.jsonl",
        help="Arquivo JSONL do corpus a atualizar (in-place).",
    )
    args = parser.parse_args()

    corpus_path = Path(args.corpus)
    entries = regenerate(corpus_path)

    with corpus_path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Corpus atualizado em {corpus_path}")


if __name__ == "__main__":
    main()
