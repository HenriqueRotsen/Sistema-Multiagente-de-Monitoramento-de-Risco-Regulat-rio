"""
Testes para persistência SQLite do DocumentRepository.
"""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.utils.data_collection import DocumentRepository


class TestDocumentRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.repo = DocumentRepository(str(self.db_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_document_and_duplicate_detection(self):
        document = {
            "id": "doc-1",
            "title": "Circular de teste",
            "source": "BCB",
            "document_type": "Circular",
            "url": "https://example.com/doc-1",
            "content": "As instituições deverão atualizar controles.",
            "published_date": datetime(2026, 1, 10),
            "metadata": {"channel": "unit-test"},
        }
        inserted = self.repo.add_document(document)

        self.assertTrue(inserted)
        self.assertTrue(self.repo.check_duplicate(url=document["url"]))
        self.assertTrue(self.repo.check_duplicate(doc_id=document["id"]))

    def test_save_extraction_and_alert_review_flow(self):
        document = {
            "id": "doc-2",
            "title": "Resolução de segurança",
            "source": "BCB",
            "document_type": "Resolução",
            "url": "https://example.com/doc-2",
            "content": "Texto regulatório de teste.",
            "published_date": datetime(2026, 2, 10),
            "metadata": {},
        }
        self.repo.add_document(document)

        extraction = {
            "document_id": "doc-2",
            "summary": "Resumo teste",
            "confidence_scores": {"summary": 0.8, "impact": 0.7},
            "extraction_method": "llm",
        }
        self.assertTrue(self.repo.save_extraction("doc-2", extraction))

        alert = {
            "alert_id": "ALR-1",
            "created_at": datetime.now().isoformat(),
            "priority": "ALTO",
            "human_reviewed": False,
            "document_title": "Resolução de segurança",
            "regulatory_body": "BCB",
            "summary": "Resumo",
            "source_url": "https://example.com/doc-2",
            "document_type": "Resolução",
            "affected_activities": [],
            "obligations": [],
            "confidence_level": "MÉDIA",
            "impact_assessment": "",
            "recommendations": [],
            "days_until_deadline": None,
            "effective_date": None,
            "implementation_deadline": None,
        }
        self.assertTrue(self.repo.save_alert("doc-2", alert))

        alerts = self.repo.get_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertFalse(alerts[0]["human_reviewed"])

        self.assertTrue(self.repo.mark_alert_reviewed("ALR-1", "ok"))
        reviewed_alerts = self.repo.get_alerts()
        self.assertTrue(reviewed_alerts[0]["human_reviewed"])

    def test_archive_alert(self):
        alert = {
            "alert_id": "ALR-ARCH",
            "created_at": datetime.now().isoformat(),
            "priority": "MÉDIO",
            "human_reviewed": False,
            "document_title": "Teste de arquivamento",
            "regulatory_body": "CVM",
            "summary": "Alerta para arquivar",
            "source_url": "https://example.com/arch",
            "document_type": "Instrução",
            "affected_activities": [],
            "obligations": [],
            "confidence_level": "BAIXA",
            "impact_assessment": "",
            "recommendations": [],
            "days_until_deadline": None,
            "effective_date": None,
            "implementation_deadline": None,
        }
        self.repo.save_alert(None, alert)

        # Alerta visível antes de arquivar
        before = self.repo.get_alerts(include_archived=False)
        self.assertEqual(len(before), 1)

        # Arquiva o alerta
        self.assertTrue(self.repo.archive_alert("ALR-ARCH"))

        # Não aparece mais na lista principal
        after = self.repo.get_alerts(include_archived=False)
        self.assertEqual(len(after), 0)

        # Aparece quando include_archived=True
        all_alerts = self.repo.get_alerts(include_archived=True)
        self.assertEqual(len(all_alerts), 1)

    def test_monitoring_cycle_history(self):
        cycle = {
            "cycle_id": "cycle-001",
            "started_at": datetime.now().isoformat(),
            "finished_at": datetime.now().isoformat(),
            "documents_collected": 5,
            "documents_analyzed": 4,
            "alerts_generated": 3,
            "errors": [],
            "summary": {"by_priority": {"ALTO": 2}},
        }
        saved = self.repo.save_monitoring_cycle(cycle)
        self.assertTrue(saved)

        history = self.repo.get_monitoring_cycles(limit=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["cycle_id"], "cycle-001")
        self.assertEqual(history[0]["alerts_generated"], 3)


if __name__ == "__main__":
    unittest.main()
