"""
Testes para Monitor Agent
"""
import unittest
from src.agents.monitor_agent import MonitorAgent, RegulatoryDocument
from datetime import datetime


class TestMonitorAgent(unittest.TestCase):
    """Testes do Monitor Agent"""
    
    def setUp(self):
        self.monitor = MonitorAgent()
    
    def test_initialization(self):
        """Testa inicialização do agente"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(len(self.monitor.sources), 2)
        self.assertIn("BCB", self.monitor.sources)
        self.assertIn("CVM", self.monitor.sources)
    
    def test_eliminate_duplicates(self):
        """Testa eliminação de documentos duplicados"""
        docs = [
            RegulatoryDocument(
                id="doc1",
                title="Circular 1",
                source="BCB",
                document_type="Circular",
                published_date=datetime.now(),
                url="http://test.com/1",
                content="Content"
            ),
            RegulatoryDocument(
                id="doc2",
                title="Circular 1",
                source="BCB",
                document_type="Circular",
                published_date=datetime.now(),
                url="http://test.com/2",
                content="Content"
            )
        ]
        
        unique = self.monitor.eliminate_duplicates(docs)
        self.assertEqual(len(unique), 1)
    
    def test_initial_screening(self):
        """Testa triagem inicial de documentos"""
        docs = [
            RegulatoryDocument(
                id="doc1",
                title="Circular 1",
                source="BCB",
                document_type="Circular",
                published_date=datetime.now(),
                url="http://test.com",
                content="Content"
            ),
            RegulatoryDocument(
                id="doc2",
                title="Newsletter",
                source="BCB",
                document_type="Newsletter",
                published_date=datetime.now(),
                url="http://test.com",
                content="Content"
            )
        ]
        
        screened = self.monitor.initial_screening(docs)
        self.assertEqual(len(screened), 1)
        self.assertEqual(screened[0].document_type, "Circular")
    
    def test_update_processed(self):
        """Testa marcação de documento como processado"""
        self.monitor.update_processed("doc_test")
        self.assertIn("doc_test", self.monitor.processed_docs)
    
    def test_get_status(self):
        """Testa obtenção de status do monitor"""
        status = self.monitor.get_status()
        self.assertIn("total_processed", status)
        self.assertIn("sources", status)
        self.assertIn("last_update", status)


if __name__ == '__main__':
    unittest.main()
