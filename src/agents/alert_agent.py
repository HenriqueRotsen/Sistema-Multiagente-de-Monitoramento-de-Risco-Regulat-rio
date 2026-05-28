"""
Alert Agent - Gera alertas estruturados para triagem humana
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
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
        alert_id = f"ALR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
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
            
            if days < 7 or impact_score > 0.9:
                return AlertPriority.CRITICAL
            elif days < 30 or impact_score > 0.7:
                return AlertPriority.HIGH
            elif days < 90:
                return AlertPriority.MEDIUM
        
        return AlertPriority.LOW

    def _generate_summary(self, info: Dict[str, Any]) -> str:
        """
        TODO: Implementar sumarização customizada
        - Formato: "O {regulador} {ação} {tema} ({deadline})"
        - Exemplo: "O BCB requer autenticação MFA em plataformas de pagamento (prazo: 31/12/2024)"
        """
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
        TODO: Implementar geração de recomendações iniciais
        - Baseado em tipo de obrigação
        - Recomendações genéricas por setor
        - Formato: ação inicial para triagem
        """
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
║ 📋 ATIVIDADES AFETADAS:
"""
        for activity in alert.affected_activities:
            output += f"║    • {activity}\n"
        
        output += f"║\n║ 📌 OBRIGAÇÕES:\n"
        for obligation in alert.obligations[:3]:  # Primeiras 3
            output += f"║    • {obligation[:70]}\n"
        
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
        TODO: Implementar exportação em múltiplos formatos
        - JSON: para sistemas automatizados
        - PDF: para relatórios
        - CSV: para planilhas
        - HTML: para portal
        """
        if format == "json":
            return json.dumps(
                [a.to_dict() for a in alerts],
                ensure_ascii=False,
                indent=2
            )
        else:
            return "Formato não implementado"

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
