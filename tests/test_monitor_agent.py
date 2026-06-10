"""
Testes para Monitor Agent
"""
import unittest
from src.agents.monitor_agent import MonitorAgent, RegulatoryDocument
from datetime import datetime
from unittest.mock import patch


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

    @patch.object(MonitorAgent, "_parse_rss_entries")
    def test_fetch_bcb_documents_from_rss(self, mock_parse):
        """Testa coleta e filtragem de itens regulatórios do RSS do BCB"""
        mock_parse.return_value = [
            {
                "title": "BCB publica Resolução BCB nº 123",
                "summary": "<p>Nova regra para instituições de pagamento.</p>",
                "link": "https://www.bcb.gov.br/teste/resolucao-123",
                "published": "Tue, 28 May 2024 10:00:00 -0300",
            },
            {
                "title": "BCB divulga agenda semanal",
                "summary": "Notícia institucional sem ato normativo.",
                "link": "https://www.bcb.gov.br/teste/agenda",
                "published": "Tue, 28 May 2024 11:00:00 -0300",
            },
        ]

        docs = self.monitor._fetch_bcb_documents("https://www.bcb.gov.br/htms/novidades/ult_noticias.xml")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source, "BCB")
        self.assertEqual(docs[0].document_type, "Resolução")
        self.assertEqual(docs[0].content, "Nova regra para instituições de pagamento.")
        self.assertTrue(docs[0].id.startswith("bcb-"))

    @patch.object(MonitorAgent, "_parse_bcb_entries")
    def test_fetch_bcb_documents_from_current_api(self, mock_parse):
        """Testa coleta usando o formato normalizado da API atual do BCB"""
        mock_parse.return_value = [
            {
                "title": "Utilização de imóvel como garantia já está regulamentada",
                "summary": "O CMN editou a Resolução CMN 5.197 para operações de crédito.",
                "link": "https://www.bcb.gov.br/detalhenoticia/20548/noticia",
                "published": "2025-02-17T12:44:31Z",
                "id": "20548",
            }
        ]

        docs = self.monitor._fetch_bcb_documents(
            "https://www.bcb.gov.br/api/servico/sitebcb/noticias?quantidade=20"
        )

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].document_type, "Resolução")
        self.assertEqual(docs[0].published_date.year, 2025)
        self.assertEqual(docs[0].url, "https://www.bcb.gov.br/detalhenoticia/20548/noticia")
    
    def test_get_status(self):
        """Testa obtenção de status do monitor"""
        status = self.monitor.get_status()
        self.assertIn("total_processed", status)
        self.assertIn("sources", status)
        self.assertIn("last_update", status)


if __name__ == '__main__':
    unittest.main()
