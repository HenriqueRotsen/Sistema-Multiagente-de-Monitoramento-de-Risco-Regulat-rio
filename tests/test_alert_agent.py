"""
Testes para Alert Agent
"""
import unittest
from datetime import datetime

from src.agents.alert_agent import AlertAgent, AlertPriority


class TestAlertAgent(unittest.TestCase):
    """Testes do Alert Agent"""

    def test_alert_uses_llm_summary_impact_and_recommendations(self):
        agent = AlertAgent()
        alert = agent.generate_alert(
            {
                "regulatory_body": "BCB",
                "title": "Circular de pagamentos",
                "document_type": "Circular",
                "source_url": "https://example.com",
                "summary": "Resumo objetivo produzido pelo LLM.",
                "affected_activities": ["Processamento de pagamentos"],
                "obligations": ["Instituições deverão atualizar controles."],
                "impact_score": 0.8,
                "impact_description": "Impacto alto em processos operacionais.",
                "recommendations": ["Abrir plano de adequação regulatória."],
                "confidence_scores": {
                    "summary": 0.9,
                    "dates": 0.7,
                    "obligations": 0.8,
                    "impact": 0.8,
                },
            }
        )

        self.assertEqual(alert.summary, "Resumo objetivo produzido pelo LLM.")
        self.assertEqual(alert.impact_assessment, "Impacto alto em processos operacionais.")
        self.assertEqual(alert.recommendations, ["Abrir plano de adequação regulatória."])

        display = agent.format_for_display(alert)
        self.assertIn("Resumo objetivo produzido pelo LLM.", display)
        self.assertIn("Impacto alto em processos operacionais.", display)
        self.assertIn("Abrir plano de adequação regulatória.", display)

    def test_past_deadline_does_not_force_critical_priority(self):
        agent = AlertAgent()
        alert = agent.generate_alert(
            {
                "regulatory_body": "BCB",
                "title": "Norma antiga",
                "document_type": "Resolução",
                "source_url": "https://example.com",
                "summary": "Resumo.",
                "implementation_deadline": datetime(2020, 1, 1),
                "impact_score": 0.4,
                "confidence_scores": {"summary": 0.8, "dates": 0.8, "obligations": 0.0, "impact": 0.4},
            }
        )

        self.assertEqual(alert.priority, AlertPriority.LOW)

    def test_export_alerts_html_and_pdf(self):
        agent = AlertAgent()
        alert = agent.generate_alert(
            {
                "regulatory_body": "BCB",
                "title": "Circular de teste",
                "document_type": "Circular",
                "source_url": "https://example.com",
                "summary": "Resumo de teste",
                "obligations": ["Instituições deverão atualizar controles."],
                "affected_activities": ["Processamento de pagamentos"],
                "confidence_scores": {"summary": 0.8, "dates": 0.7, "obligations": 0.8, "impact": 0.6},
            }
        )

        html_output = agent.export_alerts([alert], format="html")
        pdf_output = agent.export_alerts([alert], format="pdf")

        self.assertIn("<html", html_output.lower())
        self.assertTrue(pdf_output.startswith(b"%PDF"))

    def test_export_cycle_report_formats(self):
        agent = AlertAgent()
        cycle = {
            "cycle_id": "cycle-test",
            "started_at": "2026-06-26T09:00:00",
            "finished_at": "2026-06-26T09:01:00",
            "documents_collected": 2,
            "documents_analyzed": 2,
            "alerts_generated": 1,
            "errors": [],
            "summary": {"by_priority": {"ALTO": 1}},
            "alerts": [
                {
                    "alert_id": "ALR-1",
                    "priority": "ALTO",
                    "regulatory_body": "BCB",
                    "document_title": "Circular teste",
                    "summary": "Resumo",
                    "impact_assessment": "Impacto alto",
                    "human_reviewed": False,
                }
            ],
        }

        html_output = agent.export_cycle_report(cycle, format="html")
        pdf_output = agent.export_cycle_report(cycle, format="pdf")
        self.assertIn("Relatório consolidado do ciclo", html_output)
        self.assertTrue(pdf_output.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
