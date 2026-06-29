"""
Testes para Monitor Agent
"""
import unittest
import tempfile
from pathlib import Path
from src.agents.monitor_agent import MonitorAgent, RegulatoryDocument
from datetime import datetime
from unittest.mock import patch
from urllib.error import URLError


class TestMonitorAgent(unittest.TestCase):
    """Testes do Monitor Agent"""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.monitor = MonitorAgent(str(Path(self.temp_dir.name) / "monitor.db"))

    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """Testa inicialização do agente"""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(len(self.monitor.sources), 2)
        self.assertIn("BCB", self.monitor.sources)
        self.assertIn("CVM", self.monitor.sources)

    def test_default_bcb_history_limit_and_override(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "monitor.db"
            with patch.dict(
                "os.environ",
                {
                    "BCB_HISTORY_LIMIT": "200",
                    "BCB_NEWS_API_URL": "",
                    "BCB_RSS_URL": "",
                },
            ):
                monitor = MonitorAgent(str(db_path))

            self.assertEqual(monitor.bcb_history_limit, 200)
            self.assertIn("quantidade=200", monitor.sources["BCB"])

    @patch.object(MonitorAgent, "_parse_cvm_legislation_page")
    def test_default_cvm_history_uses_twenty_pages(self, mock_parse):
        mock_parse.side_effect = [
            ([], f"https://example.com/cvm?page={page + 1}")
            for page in range(1, 21)
        ]
        with patch.dict("os.environ", {"CVM_MAX_PAGES": "20"}):
            self.monitor._fetch_cvm_documents("https://example.com/cvm?page=1")

        self.assertEqual(mock_parse.call_count, 20)
    
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

    @patch.object(MonitorAgent, "_parse_cvm_legislation_page")
    def test_fetch_cvm_documents_from_legislation(self, mock_parse):
        """Testa coleta CVM com filtro de tipos regulatórios."""
        mock_parse.return_value = (
            [
                {
                    "title": "Resolução CVM 244",
                    "summary": "Altera norma anterior para emissores.",
                    "document_type": "Resoluções",
                    "published": "29/05/2026",
                    "link": "https://conteudo.cvm.gov.br/legislacao/resolucoes/resol244.html",
                },
                {
                    "title": "Portaria CVM/PTE Nº 139/2026",
                    "summary": "Ato administrativo interno.",
                    "document_type": "Portarias",
                    "published": "12/06/2026",
                    "link": "https://conteudo.cvm.gov.br/legislacao/portarias/pte139.html",
                },
            ],
            None,
        )

        docs = self.monitor._fetch_cvm_documents("https://conteudo.cvm.gov.br/legislacao/index.html")

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source, "CVM")
        self.assertEqual(docs[0].document_type, "Resolução")
        self.assertEqual(docs[0].published_date.year, 2026)
        self.assertIn("resol244", docs[0].url)
    
    def test_get_status(self):
        """Testa obtenção de status do monitor"""
        status = self.monitor.get_status()
        self.assertIn("total_processed", status)
        self.assertIn("sources", status)
        self.assertIn("last_update", status)

    @patch("src.agents.monitor_agent.time.sleep")
    @patch("src.agents.monitor_agent.urlopen")
    def test_open_url_with_retry(self, mock_urlopen, _mock_sleep):
        """Testa retry com backoff para coleta de fontes."""
        mock_response = object()
        mock_urlopen.side_effect = [URLError("temp"), mock_response]

        result = self.monitor._open_url_with_retry("https://example.com", timeout=5)

        self.assertIs(result, mock_response)
        self.assertEqual(mock_urlopen.call_count, 2)


if __name__ == '__main__':
    unittest.main()
