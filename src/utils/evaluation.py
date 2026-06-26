"""
Métricas de qualidade para extração regulatória.
"""
from __future__ import annotations

from datetime import datetime
import math
import re
from typing import Any, Dict, List, Optional


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return num / den


def classification_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _parse_date(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def date_accuracy(pairs: List[tuple[Any, Any]]) -> float:
    valid = 0
    correct = 0
    for predicted, expected in pairs:
        expected_dt = _parse_date(expected)
        if expected_dt is None:
            continue
        predicted_dt = _parse_date(predicted)
        valid += 1
        if predicted_dt and predicted_dt.date() == expected_dt.date():
            correct += 1
    return _safe_div(correct, valid)


def mean_deadline_error_days(pairs: List[tuple[Any, Any]]) -> Optional[float]:
    errors = []
    for predicted, expected in pairs:
        predicted_dt = _parse_date(predicted)
        expected_dt = _parse_date(expected)
        if predicted_dt and expected_dt:
            errors.append(abs((predicted_dt.date() - expected_dt.date()).days))
    if not errors:
        return None
    return sum(errors) / len(errors)


def _normalize_text(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())
    return " ".join(normalized.split())


def _token_set(text: str) -> set[str]:
    return set(_normalize_text(text).split())


def _best_match_score(item: str, candidates: List[str]) -> float:
    item_tokens = _token_set(item)
    if not item_tokens:
        return 0.0
    best = 0.0
    for candidate in candidates:
        cand_tokens = _token_set(candidate)
        if not cand_tokens:
            continue
        inter = len(item_tokens & cand_tokens)
        union = len(item_tokens | cand_tokens)
        score = _safe_div(inter, union)
        if score > best:
            best = score
    return best


def obligation_accuracy(predicted: List[str], expected: List[str], threshold: float = 0.5) -> Dict[str, float]:
    if not expected and not predicted:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    tp = 0
    for exp in expected:
        if _best_match_score(exp, predicted) >= threshold:
            tp += 1
    fp = max(0, len(predicted) - tp)
    fn = max(0, len(expected) - tp)
    return classification_metrics(tp, fp, fn)


def evaluate_corpus_predictions(
    corpus_entries: List[Dict[str, Any]],
    predictions_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    relevance_tp = relevance_fp = relevance_fn = 0
    effective_date_pairs: List[tuple[Any, Any]] = []
    deadline_pairs: List[tuple[Any, Any]] = []
    obligation_scores: List[Dict[str, float]] = []

    for entry in corpus_entries:
        gold = entry.get("gold", {})
        predicted = predictions_by_id.get(entry.get("id"), {})
        gold_relevance = bool(gold.get("relevance", False))
        pred_relevance = bool(predicted.get("impact_score", 0.0) >= 0.5)

        if pred_relevance and gold_relevance:
            relevance_tp += 1
        elif pred_relevance and not gold_relevance:
            relevance_fp += 1
        elif (not pred_relevance) and gold_relevance:
            relevance_fn += 1

        effective_date_pairs.append((predicted.get("effective_date"), gold.get("effective_date")))
        deadline_pairs.append((predicted.get("implementation_deadline"), gold.get("implementation_deadline")))
        obligation_scores.append(
            obligation_accuracy(
                predicted=predicted.get("obligations", []) or [],
                expected=gold.get("obligations", []) or [],
            )
        )

    relevance = classification_metrics(relevance_tp, relevance_fp, relevance_fn)
    date_acc_effective = date_accuracy(effective_date_pairs)
    date_acc_deadline = date_accuracy(deadline_pairs)
    date_acc_all = _safe_div(date_acc_effective + date_acc_deadline, 2)

    obligation_precision = _safe_div(
        sum(score["precision"] for score in obligation_scores),
        len(obligation_scores) or 1,
    )
    obligation_recall = _safe_div(
        sum(score["recall"] for score in obligation_scores),
        len(obligation_scores) or 1,
    )
    obligation_f1 = _safe_div(
        sum(score["f1"] for score in obligation_scores),
        len(obligation_scores) or 1,
    )

    deadline_error = mean_deadline_error_days(deadline_pairs)

    return {
        "sample_size": len(corpus_entries),
        "relevance": relevance,
        "date_accuracy": {
            "effective_date": date_acc_effective,
            "implementation_deadline": date_acc_deadline,
            "overall": date_acc_all,
        },
        "obligations": {
            "precision": obligation_precision,
            "recall": obligation_recall,
            "f1": obligation_f1,
        },
        "deadline_error_days_mean": deadline_error,
    }
