"""
Testes para cliente LLM
"""
import unittest
from unittest.mock import Mock, patch
import requests

from src.utils.llm_integration import RegulatoryLLM, RegulatoryLLMConfig


class TestRegulatoryLLM(unittest.TestCase):
    """Testes do cliente RegulatoryLLM"""

    @patch("src.utils.llm_integration.requests.post")
    def test_ollama_chat_uses_api_key_header(self, mock_post):
        response = Mock()
        response.json.return_value = {
            "message": {
                "content": '{"summary":"ok","impact_score":0.4}'
            }
        }
        response.raise_for_status.return_value = None
        mock_post.return_value = response

        llm = RegulatoryLLM(
            RegulatoryLLMConfig(
                base_url="https://ollama.futurelab.dcc.ufmg.br",
                model="llama3.2:3b",
                provider="ollama",
                api_key="abc123",
            )
        )

        result = llm.analyze_regulation("Texto", {"title": "Teste"}, {"name": "Setor"})

        self.assertEqual(result["summary"], "ok")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["X-API-Key"], "abc123")
        self.assertEqual(kwargs["json"]["model"], "llama3.2:3b")
        self.assertEqual(kwargs["json"]["stream"], False)

    def test_parse_json_inside_text(self):
        llm = RegulatoryLLM(
            RegulatoryLLMConfig(
                base_url="https://ollama.futurelab.dcc.ufmg.br",
                model="llama3.2:3b",
            )
        )

        parsed = llm._parse_json_object('Resposta:\n{"summary":"ok","impact_score":0.2}')
        self.assertEqual(parsed["summary"], "ok")

    @patch("src.utils.llm_integration.time.sleep")
    @patch("src.utils.llm_integration.requests.post")
    def test_llm_retry_with_backoff(self, mock_post, mock_sleep):
        first_error = requests.Timeout("timeout")
        ok_response = Mock()
        ok_response.raise_for_status.return_value = None
        ok_response.json.return_value = {"message": {"content": '{"summary":"ok","impact_score":0.4}'}}
        mock_post.side_effect = [first_error, ok_response]

        llm = RegulatoryLLM(
            RegulatoryLLMConfig(
                base_url="https://ollama.futurelab.dcc.ufmg.br",
                model="llama3.2:3b",
                provider="ollama",
                max_retries=2,
                retry_backoff_seconds=0.5,
            )
        )

        result = llm.analyze_regulation("Texto", {"title": "Teste"}, {"name": "Setor"})
        self.assertEqual(result["summary"], "ok")
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called()


if __name__ == "__main__":
    unittest.main()
