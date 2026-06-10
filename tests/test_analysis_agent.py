"""
Testes para Analysis Agent
"""
import unittest

from src.agents.analysis_agent import AnalysisAgent


class FakeLLM:
    """LLM fake para testar integração sem rede."""

    def analyze_regulation(self, text, metadata, sector_profile):
        return {
            "summary": "Resumo estruturado pelo LLM.",
            "effective_date": "2025-01-01",
            "implementation_deadline": "2025-06-30",
            "affected_activities": ["Processamento de pagamentos"],
            "affected_entities": ["instituições de pagamento"],
            "obligations": ["Instituições deverão adequar sistemas de pagamento."],
            "recommendations": ["Abrir plano de adequação com compliance e tecnologia."],
            "keywords": ["pagamento", "pix"],
            "impact_score": 0.82,
            "impact_description": "Alto impacto operacional.",
            "impact_areas": ["Compliance", "Tecnologia"],
            "confidence_scores": {
                "summary": 0.9,
                "dates": 0.8,
                "obligations": 0.85,
                "impact": 0.8,
            },
        }


class TestAnalysisAgent(unittest.TestCase):
    """Testes do Analysis Agent"""

    def test_analyze_document_with_llm(self):
        agent = AnalysisAgent(llm_model=FakeLLM())
        result = agent.analyze_document(
            "Texto regulatório de teste.",
            {
                "id": "doc1",
                "source": "BCB",
                "document_type": "Resolução",
                "title": "Resolução de pagamentos",
                "url": "https://example.com",
            },
        )

        self.assertEqual(result.extraction_method, "llm")
        self.assertEqual(result.summary, "Resumo estruturado pelo LLM.")
        self.assertEqual(result.implementation_deadline.year, 2025)
        self.assertEqual(result.obligations, ["Instituições deverão adequar sistemas de pagamento."])
        self.assertEqual(result.recommendations, ["Abrir plano de adequação com compliance e tecnologia."])
        self.assertEqual(result.impact_score, 0.82)

    def test_analyze_document_fallback_without_llm(self):
        agent = AnalysisAgent()
        result = agent.analyze_document(
            "As instituições de pagamento deverão atualizar seus controles até 30/06/2025.",
            {
                "id": "doc2",
                "source": "BCB",
                "document_type": "Circular",
                "title": "Circular de teste",
            },
        )

        self.assertEqual(result.extraction_method, "regex")
        self.assertTrue(result.obligations)
        self.assertEqual(result.implementation_deadline.year, 2025)
        self.assertGreater(result.impact_score, 0.3)


if __name__ == "__main__":
    unittest.main()
