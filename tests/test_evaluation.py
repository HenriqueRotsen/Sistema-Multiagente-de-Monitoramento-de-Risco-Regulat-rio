"""
Testes de métricas de qualidade da análise.
"""
import unittest

from src.utils.evaluation import (
    classification_metrics,
    date_accuracy,
    evaluate_corpus_predictions,
    obligation_accuracy,
)


class TestEvaluationMetrics(unittest.TestCase):
    def test_classification_metrics(self):
        metrics = classification_metrics(tp=8, fp=2, fn=2)
        self.assertAlmostEqual(metrics["precision"], 0.8)
        self.assertAlmostEqual(metrics["recall"], 0.8)
        self.assertAlmostEqual(metrics["f1"], 0.8)

    def test_date_accuracy(self):
        pairs = [
            ("2026-06-30", "2026-06-30"),
            ("2026-07-01", "2026-06-30"),
            (None, "2026-01-01"),
        ]
        self.assertAlmostEqual(date_accuracy(pairs), 1 / 3)

    def test_obligation_accuracy(self):
        metrics = obligation_accuracy(
            predicted=["Instituições deverão atualizar controles antifraude até 30/06/2026."],
            expected=["As instituições deverão atualizar controles antifraude até 30/06/2026."],
        )
        self.assertGreater(metrics["f1"], 0.5)

    def test_evaluate_corpus_predictions(self):
        corpus = [
            {
                "id": "doc-1",
                "gold": {
                    "relevance": True,
                    "effective_date": None,
                    "implementation_deadline": "2026-06-30",
                    "obligations": ["Instituições deverão atualizar controles."],
                },
            }
        ]
        preds = {
            "doc-1": {
                "impact_score": 0.9,
                "effective_date": None,
                "implementation_deadline": "2026-06-30",
                "obligations": ["Instituições deverão atualizar controles."],
            }
        }
        report = evaluate_corpus_predictions(corpus, preds)
        self.assertEqual(report["sample_size"], 1)
        self.assertAlmostEqual(report["relevance"]["f1"], 1.0)
        self.assertAlmostEqual(report["date_accuracy"]["implementation_deadline"], 1.0)


if __name__ == "__main__":
    unittest.main()
