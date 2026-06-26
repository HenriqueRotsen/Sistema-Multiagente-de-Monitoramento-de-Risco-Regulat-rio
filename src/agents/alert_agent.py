"""
Alert Agent - Gera alertas estruturados para triagem humana
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import csv
from html import escape
from io import StringIO
import json
import logging

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Níveis de prioridade de alerta"""
    CRITICAL = "CRÍTICO"       # Prazo < 7 dias
    HIGH = "ALTO"              # Prazo 7-30 dias  
    MEDIUM = "MÉDIO"           # Prazo 30-90 dias
    LOW = "BAIXO"              # Prazo > 90 dias


@dataclass
class StructuredAlert:
    """Alerta estruturado gerado pelo sistema"""
    alert_id: str
    created_at: datetime
    
    # Informações do documento
    regulatory_body: str  # BCB, CVM
    document_title: str
    document_type: str
    source_url: str
    
    # Conteúdo do alerta
    summary: str
    priority: AlertPriority
    affected_activities: List[str]
    obligations: List[str]
    
    # Datas importantes
    effective_date: Optional[datetime] = None
    implementation_deadline: Optional[datetime] = None
    days_until_deadline: Optional[int] = None
    
    # Rastreabilidade
    confidence_level: str = "MÉDIA"  # ALTA, MÉDIA, BAIXA
    impact_assessment: str = ""
    recommendations: List[str] = None
    
    # Validação humana
    human_reviewed: bool = False
    reviewer_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa alerta para dicionário"""
        return {
            'alert_id': self.alert_id,
            'created_at': self.created_at.isoformat(),
            'regulatory_body': self.regulatory_body,
            'document_title': self.document_title,
            'document_type': self.document_type,
            'source_url': self.source_url,
            'summary': self.summary,
            'priority': self.priority.value,
            'affected_activities': self.affected_activities,
            'obligations': self.obligations,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'implementation_deadline': self.implementation_deadline.isoformat() if self.implementation_deadline else None,
            'days_until_deadline': self.days_until_deadline,
            'confidence_level': self.confidence_level,
            'impact_assessment': self.impact_assessment,
            'recommendations': self.recommendations or [],
            'human_reviewed': self.human_reviewed,
        }

    def to_json(self) -> str:
        """Serializa para JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AlertAgent:
    """
    Agente responsável por:
    1. Consolidar dados extraídos
    2. Priorizar por urgência
    3. Gerar alertas estruturados
    4. Formatar para triagem humana
    """

    def __init__(self):
        self.generated_alerts = []
        self.alert_templates = self._get_templates()

    def generate_alert(self, extracted_info: Dict[str, Any]) -> StructuredAlert:
        """
        Gera um alerta estruturado a partir de informações extraídas
        """
        alert_id = f"ALR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        # Determina prioridade
        priority = self._determine_priority(extracted_info)
        
        # Calcula dias até deadline
        days_until = None
        if extracted_info.get('implementation_deadline'):
            delta = extracted_info['implementation_deadline'] - datetime.now()
            days_until = delta.days
        
        alert = StructuredAlert(
            alert_id=alert_id,
            created_at=datetime.now(),
            regulatory_body=extracted_info.get('regulatory_body', ''),
            document_title=extracted_info.get('title', ''),
            document_type=extracted_info.get('document_type', ''),
            source_url=extracted_info.get('source_url', ''),
            summary=self._generate_summary(extracted_info),
            priority=priority,
            affected_activities=extracted_info.get('affected_activities', []),
            obligations=extracted_info.get('obligations', []),
            effective_date=extracted_info.get('effective_date'),
            implementation_deadline=extracted_info.get('implementation_deadline'),
            days_until_deadline=days_until,
            confidence_level=self._assess_confidence(extracted_info),
            impact_assessment=extracted_info.get('impact_description', ''),
            recommendations=self._generate_recommendations(extracted_info)
        )
        
        self.generated_alerts.append(alert)
        return alert

    def _determine_priority(self, info: Dict[str, Any]) -> AlertPriority:
        """
        Determina prioridade baseado em:
        - Prazo de implementação
        - Score de impacto
        - Tipo de obrigação
        """
        deadline = info.get('implementation_deadline')
        impact_score = info.get('impact_score', 0.5)
        
        if deadline:
            delta = deadline - datetime.now()
            days = delta.days

            if days < 0:
                return AlertPriority.LOW
            
            if days < 7 or impact_score > 0.9:
                return AlertPriority.CRITICAL
            elif days < 30 or impact_score > 0.7:
                return AlertPriority.HIGH
            elif days < 90:
                return AlertPriority.MEDIUM
        
        return AlertPriority.LOW

    def _generate_summary(self, info: Dict[str, Any]) -> str:
        """
        Usa resumo extraído pelo Analysis Agent/LLM quando disponível.
        """
        extracted_summary = info.get('summary', '')
        if extracted_summary:
            return extracted_summary

        template = "Alerta: {title} - Regulador: {body}"
        return template.format(
            title=info.get('title', 'Alteração regulatória'),
            body=info.get('regulatory_body', 'BCB/CVM')
        )

    def _assess_confidence(self, info: Dict[str, Any]) -> str:
        """Avalia confiança das informações extraídas"""
        confidence_scores = info.get('confidence_scores', {})
        
        if not confidence_scores:
            return "BAIXA"
        
        avg_score = sum(confidence_scores.values()) / len(confidence_scores)
        
        if avg_score >= 0.8:
            return "ALTA"
        elif avg_score >= 0.6:
            return "MÉDIA"
        else:
            return "BAIXA"

    def _generate_recommendations(self, info: Dict[str, Any]) -> List[str]:
        """
        Usa recomendações vindas da análise e aplica fallback simples.
        """
        extracted_recommendations = info.get('recommendations', [])
        if extracted_recommendations:
            return extracted_recommendations

        recommendations = []
        
        activities = info.get('affected_activities', [])
        if "Open Banking" in activities:
            recommendations.append("Revisar conformidade com padrões Open Banking")
        
        if "Autenticação" in activities:
            recommendations.append("Avaliar segurança de autenticação atual")
        
        return recommendations or ["Revisar com especialista em compliance regulatório"]

    def prioritize_alerts(self, alerts: List[StructuredAlert]) -> List[StructuredAlert]:
        """Ordena alertas por prioridade e urgência"""
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3
        }
        
        return sorted(
            alerts,
            key=lambda a: (
                priority_order.get(a.priority, 99),
                a.days_until_deadline if a.days_until_deadline else 999
            )
        )

    def format_for_display(self, alert: StructuredAlert) -> str:
        """Formata alerta para exibição em interface/relatório"""
        output = f"""
╔{'═' * 80}╗
║ ALERTA REGULATÓRIO #{alert.alert_id:<65}║
╠{'═' * 80}╣
║
║ 🏛️  REGULADOR:        {alert.regulatory_body:<50}
║ 📄 DOCUMENTO:        {alert.document_title[:50]:<50}
║ 🏷️  TIPO:             {alert.document_type:<50}
║ ⚠️  PRIORIDADE:       {alert.priority.value:<50}
║
║ 🧾 RESUMO:
"""
        output += self._format_bulleted_text(alert.summary, width=74, prefix="║    ")

        if alert.impact_assessment:
            output += "║\n║ 📊 IMPACTO:\n"
            output += self._format_bulleted_text(alert.impact_assessment, width=74, prefix="║    ")

        output += f"""║
║ 📋 ATIVIDADES AFETADAS:
"""
        for activity in alert.affected_activities:
            output += f"║    • {activity}\n"
        
        output += f"║\n║ 📌 OBRIGAÇÕES:\n"
        for obligation in alert.obligations[:3]:  # Primeiras 3
            output += self._format_list_item(obligation, width=70)

        output += f"║\n║ ✅ RECOMENDAÇÕES:\n"
        for recommendation in (alert.recommendations or [])[:3]:
            output += self._format_list_item(recommendation, width=70)
        
        if alert.implementation_deadline:
            output += f"║\n║ ⏰ PRAZO: {alert.implementation_deadline.strftime('%d/%m/%Y')}"
            if alert.days_until_deadline:
                output += f" ({alert.days_until_deadline} dias)"
            output += "\n"
        
        output += f"║\n║ 📊 CONFIANÇA: {alert.confidence_level}"
        output += f"\n║ 🔗 FONTE: {alert.source_url[:60]}\n"
        output += f"║ ✋ REVISÃO HUMANA: {'Sim' if alert.human_reviewed else 'Pendente'}\n"
        output += f"╚{'═' * 80}╝\n"
        
        return output

    def _format_bulleted_text(self, text: str, width: int = 74, prefix: str = "║    ") -> str:
        """Quebra texto longo em linhas curtas para o display em console."""
        if not text:
            return f"{prefix}(não informado)\n"

        words = text.split()
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)

        return "".join(f"{prefix}{line}\n" for line in lines)

    def _format_list_item(self, text: str, width: int = 70) -> str:
        """Formata item de lista preservando texto longo."""
        if not text:
            return "║    • (não informado)\n"

        wrapped = self._format_bulleted_text(text, width=width, prefix="║      ")
        lines = wrapped.splitlines()
        if not lines:
            return "║    • (não informado)\n"
        lines[0] = lines[0].replace("║      ", "║    • ", 1)
        return "\n".join(lines) + "\n"

    def batch_generate_alerts(self, analyses: List[Dict[str, Any]]) -> List[StructuredAlert]:
        """Gera alertas em lote"""
        alerts = []
        
        for analysis in analyses:
            try:
                alert = self.generate_alert(analysis)
                alerts.append(alert)
            except Exception as e:
                logger.error(f"Erro ao gerar alerta: {str(e)}")
        
        return self.prioritize_alerts(alerts)

    def _get_templates(self) -> Dict[str, str]:
        """Templates de alerta por tipo de regulação"""
        return {
            "nova_obrigacao": "O regulador {body} introduziu nova obrigação: {desc}",
            "prazo_implementacao": "Prazo de implementação para {desc}: {deadline}",
            "restricao": "Nova restrição regulatória: {desc}",
            "esclarecimento": "Esclarecimento sobre {desc}: {content}"
        }

    def export_alerts(self, alerts: List[StructuredAlert], format: str = "json") -> str:
        """
        Exporta alertas.

        Formatos suportados: JSON, CSV, HTML e PDF.
        """
        data = [a.to_dict() for a in alerts]
        if format == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        if format == "csv":
            return self._export_csv(data)
        if format == "html":
            return self._export_html(data, title="Relatório de Alertas Regulatórios")
        if format == "pdf":
            text_report = self._export_text_report(data, "Relatório de Alertas Regulatórios")
            return self._build_simple_pdf(text_report)
        raise ValueError(f"Formato não implementado: {format}")

    def export_alert_dicts(self, alerts: List[Dict[str, Any]], format: str = "json") -> str:
        """Exporta alertas já serializados (vindos de persistência)."""
        if format == "json":
            return json.dumps(alerts, ensure_ascii=False, indent=2)
        if format == "csv":
            return self._export_csv(alerts)
        if format == "html":
            return self._export_html(alerts, title="Relatório de Alertas Regulatórios")
        if format == "pdf":
            return self._build_simple_pdf(self._export_text_report(alerts, "Relatório de Alertas Regulatórios"))
        raise ValueError(f"Formato não implementado: {format}")

    def export_cycle_report(self, cycle_result: Dict[str, Any], format: str = "json") -> str:
        """Exporta relatório consolidado de um ciclo."""
        alerts = cycle_result.get("alerts", [])
        report = {
            "cycle_id": cycle_result.get("cycle_id"),
            "started_at": cycle_result.get("started_at"),
            "finished_at": cycle_result.get("finished_at"),
            "documents_collected": cycle_result.get("documents_collected", 0),
            "documents_analyzed": cycle_result.get("documents_analyzed", 0),
            "alerts_generated": cycle_result.get("alerts_generated", 0),
            "errors": cycle_result.get("errors", []),
            "summary": cycle_result.get("summary", {}),
            "alerts": alerts,
        }
        if format == "json":
            return json.dumps(report, ensure_ascii=False, indent=2)
        if format == "html":
            return self._export_cycle_html(report)
        if format == "pdf":
            text_report = self._export_cycle_text(report)
            return self._build_simple_pdf(text_report)
        raise ValueError(f"Formato não implementado para ciclo: {format}")

    def _export_csv(self, data: List[Dict[str, Any]]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "alert_id",
                "created_at",
                "priority",
                "regulatory_body",
                "document_title",
                "document_type",
                "summary",
                "impact_assessment",
                "confidence_level",
                "human_reviewed",
                "source_url",
                "affected_activities",
                "obligations",
                "recommendations",
            ]
        )
        for alert in data:
            writer.writerow(
                [
                    alert.get("alert_id", ""),
                    alert.get("created_at", ""),
                    alert.get("priority", ""),
                    alert.get("regulatory_body", ""),
                    alert.get("document_title", ""),
                    alert.get("document_type", ""),
                    alert.get("summary", ""),
                    alert.get("impact_assessment", ""),
                    alert.get("confidence_level", ""),
                    bool(alert.get("human_reviewed")),
                    alert.get("source_url", ""),
                    " | ".join(alert.get("affected_activities", [])),
                    " | ".join(alert.get("obligations", [])),
                    " | ".join(alert.get("recommendations", [])),
                ]
            )
        return output.getvalue()

    def _export_html(self, data: List[Dict[str, Any]], title: str) -> str:
        rows = []
        for alert in data:
            rows.append(
                "<tr>"
                f"<td>{escape(alert.get('alert_id', ''))}</td>"
                f"<td>{escape(alert.get('priority', ''))}</td>"
                f"<td>{escape(alert.get('regulatory_body', ''))}</td>"
                f"<td>{escape(alert.get('document_title', ''))}</td>"
                f"<td>{escape(alert.get('summary', ''))}</td>"
                f"<td>{escape(alert.get('impact_assessment', ''))}</td>"
                f"<td>{escape(str(alert.get('human_reviewed', False)))}</td>"
                "</tr>"
            )
        rows_html = "\n".join(rows)
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; }}
    th {{ background: #f0f0f0; text-align: left; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <p>Total de alertas: {len(data)}</p>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Prioridade</th><th>Regulador</th><th>Documento</th><th>Resumo</th><th>Impacto</th><th>Revisado</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>"""

    def _export_text_report(self, data: List[Dict[str, Any]], title: str) -> str:
        lines = [title, f"Total de alertas: {len(data)}", ""]
        for alert in data:
            lines.extend(
                [
                    f"- {alert.get('alert_id', '')} | {alert.get('priority', '')} | {alert.get('regulatory_body', '')}",
                    f"  Documento: {alert.get('document_title', '')}",
                    f"  Resumo: {alert.get('summary', '')}",
                    f"  Impacto: {alert.get('impact_assessment', '')}",
                    f"  Revisado: {alert.get('human_reviewed', False)}",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    def _export_cycle_html(self, report: Dict[str, Any]) -> str:
        summary = report.get("summary", {})
        by_priority = summary.get("by_priority", {})
        priority_items = "".join(
            f"<li>{escape(priority)}: {count}</li>"
            for priority, count in by_priority.items()
        )
        alerts_html = self._export_html(report.get("alerts", []), "Alertas do ciclo")
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Relatório consolidado do ciclo {escape(str(report.get("cycle_id", "")))}</title>
</head>
<body>
  <h1>Relatório consolidado do ciclo</h1>
  <p><strong>Ciclo:</strong> {escape(str(report.get("cycle_id", "")))}</p>
  <p><strong>Início:</strong> {escape(str(report.get("started_at", "")))}</p>
  <p><strong>Fim:</strong> {escape(str(report.get("finished_at", "")))}</p>
  <p><strong>Documentos coletados:</strong> {report.get("documents_collected", 0)}</p>
  <p><strong>Documentos analisados:</strong> {report.get("documents_analyzed", 0)}</p>
  <p><strong>Alertas gerados:</strong> {report.get("alerts_generated", 0)}</p>
  <h2>Distribuição por prioridade</h2>
  <ul>{priority_items}</ul>
  <h2>Alertas</h2>
  {alerts_html}
</body>
</html>"""

    def _export_cycle_text(self, report: Dict[str, Any]) -> str:
        lines = [
            f"Relatório consolidado do ciclo {report.get('cycle_id', '')}",
            f"Início: {report.get('started_at', '')}",
            f"Fim: {report.get('finished_at', '')}",
            f"Documentos coletados: {report.get('documents_collected', 0)}",
            f"Documentos analisados: {report.get('documents_analyzed', 0)}",
            f"Alertas gerados: {report.get('alerts_generated', 0)}",
            "",
            "Alertas:",
            self._export_text_report(report.get("alerts", []), "Lista de alertas"),
        ]
        return "\n".join(lines).strip() + "\n"

    def _build_simple_pdf(self, text_content: str) -> bytes:
        """Gera PDF simples a partir de texto."""
        escaped_text = text_content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        escaped_text = escaped_text.replace("\r", "")
        lines = escaped_text.split("\n")
        y = 780
        commands = ["BT", "/F1 10 Tf", "40 800 Td", "14 TL"]
        for line in lines:
            safe_line = line[:120].encode("latin-1", errors="replace").decode("latin-1")
            commands.append(f"({safe_line}) Tj")
            commands.append("T*")
            y -= 14
            if y < 40:
                commands.append("ET")
                commands.append("BT")
                commands.append("/F1 10 Tf")
                commands.append("40 800 Td")
                commands.append("14 TL")
                y = 780
        commands.append("ET")
        stream = "\n".join(commands) + "\n"

        objects = []
        objects.append("1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
        objects.append("2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n")
        objects.append(
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        )
        objects.append("4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
        objects.append(f"5 0 obj << /Length {len(stream.encode('latin-1', errors='replace'))} >> stream\n{stream}endstream endobj\n")

        pdf_header = "%PDF-1.4\n"
        offsets = [0]
        body = ""
        current_offset = len(pdf_header.encode("latin-1"))
        for obj in objects:
            offsets.append(current_offset)
            body += obj
            current_offset += len(obj.encode("latin-1", errors="replace"))

        xref_offset = current_offset
        xref_lines = ["xref", f"0 {len(offsets)}", "0000000000 65535 f "]
        for offset in offsets[1:]:
            xref_lines.append(f"{offset:010d} 00000 n ")
        xref = "\n".join(xref_lines) + "\n"
        trailer = (
            f"trailer << /Size {len(offsets)} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        )
        pdf = pdf_header + body + xref + trailer
        return pdf.encode("latin-1", errors="replace")

    def get_alert_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos alertas gerados"""
        if not self.generated_alerts:
            return {"total": 0, "by_priority": {}}
        
        by_priority = {}
        for priority in AlertPriority:
            count = sum(1 for a in self.generated_alerts if a.priority == priority)
            if count > 0:
                by_priority[priority.value] = count
        
        return {
            "total": len(self.generated_alerts),
            "by_priority": by_priority,
            "reviewed": sum(1 for a in self.generated_alerts if a.human_reviewed),
            "pending_review": sum(1 for a in self.generated_alerts if not a.human_reviewed)
        }
