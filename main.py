"""
Main orchestrator - Coordena os 3 agentes do sistema
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from src.agents.monitor_agent import MonitorAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.alert_agent import AlertAgent, StructuredAlert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegulatoryMonitoringSystem:
    """
    Orquestra o fluxo completo de monitoramento regulatório
    
    Fluxo:
    1. Monitor Agent: coleta novos documentos
    2. Analysis Agent: analisa e extrai informações
    3. Alert Agent: gera alertas estruturados
    4. Validação Humana: requer revisão antes de ação
    """

    def __init__(self):
        self.monitor_agent = MonitorAgent()
        self.analysis_agent = AnalysisAgent()
        self.alert_agent = AlertAgent()
        self.system_status = "initialized"

    def run_monitoring_cycle(self, manual_documents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executa um ciclo completo de monitoramento
        
        Args:
            manual_documents: documentos para teste (ignora coleta automática)
        
        Returns:
            Resultado do ciclo com alertas gerados
        """
        logger.info("=" * 80)
        logger.info("INICIANDO CICLO DE MONITORAMENTO REGULATÓRIO")
        logger.info("=" * 80)
        
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "documents_collected": 0,
            "documents_analyzed": 0,
            "alerts_generated": 0,
            "alerts": [],
            "errors": []
        }
        
        try:
            # ETAPA 1: COLETA
            logger.info("\n[ETAPA 1] Coletando documentos...")
            documents = self._collect_documents(manual_documents)
            cycle_result["documents_collected"] = len(documents)
            logger.info(f"✓ {len(documents)} documentos coletados")
            
            # ETAPA 2: ANÁLISE
            logger.info("\n[ETAPA 2] Analisando documentos...")
            analyses = self._analyze_documents(documents)
            cycle_result["documents_analyzed"] = len(analyses)
            logger.info(f"✓ {len(analyses)} documentos analisados")
            
            # ETAPA 3: GERAÇÃO DE ALERTAS
            logger.info("\n[ETAPA 3] Gerando alertas estruturados...")
            alerts = self._generate_alerts(analyses)
            cycle_result["alerts_generated"] = len(alerts)
            logger.info(f"✓ {len(alerts)} alertas gerados")
            
            # ETAPA 4: EXIBIÇÃO
            logger.info("\n[ETAPA 4] Alertas para Triagem Humana:")
            for alert in alerts:
                print(self.alert_agent.format_for_display(alert))
            
            cycle_result["alerts"] = [a.to_dict() for a in alerts]
            cycle_result["summary"] = self.alert_agent.get_alert_summary()
            
        except Exception as e:
            logger.error(f"Erro durante ciclo de monitoramento: {str(e)}")
            cycle_result["errors"].append(str(e))
            self.system_status = "error"
        
        logger.info("\n" + "=" * 80)
        logger.info("CICLO DE MONITORAMENTO FINALIZADO")
        logger.info("=" * 80)
        
        return cycle_result

    def _collect_documents(self, manual_documents: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Etapa 1: Coleta de documentos
        
        Usa coleta automática dos agentes quando não há documentos manuais.
        """
        if manual_documents:
            logger.info("Usando documentos manuais para teste")
            return manual_documents
        
        collected = self.monitor_agent.monitor_sources()
        unique_documents = self.monitor_agent.eliminate_duplicates(collected)
        screened_documents = self.monitor_agent.initial_screening(unique_documents)

        return [
            {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "document_type": doc.document_type,
                "published_date": doc.published_date,
                "url": doc.url,
                "content": doc.content,
                "metadata": doc.metadata or {},
            }
            for doc in screened_documents
        ]

    def _analyze_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Etapa 2: Análise de impacto regulatório"""
        analyses = []
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"  [{i}/{len(documents)}] Analisando: {doc.get('title', 'sem título')[:60]}...")
            
            # Simula análise com placeholder
            analysis = {
                "document_id": doc.get("id", f"doc_{i}"),
                "title": doc.get("title", ""),
                "source": doc.get("source", "BCB"),
                "document_type": doc.get("document_type", "Circular"),
                "regulatory_body": doc.get("source", "BCB"),
                "source_url": doc.get("url", ""),
                "content": doc.get("content", ""),
                "affected_activities": ["Processamento de pagamentos", "Open Banking"],
                "obligations": [
                    "Implementar autenticação MFA",
                    "Manter registros de transações"
                ],
                "effective_date": None,
                "implementation_deadline": None,
                "impact_score": 0.75,
                "impact_description": "Alto impacto para fintechs de pagamento",
                "confidence_scores": {
                    "summary": 0.85,
                    "dates": 0.60,
                    "obligations": 0.80,
                    "impact": 0.75
                }
            }
            
            analyses.append(analysis)
        
        return analyses

    def _generate_alerts(self, analyses: List[Dict[str, Any]]) -> List[StructuredAlert]:
        """Etapa 3: Geração de alertas"""
        alerts = self.alert_agent.batch_generate_alerts(analyses)
        return self.alert_agent.prioritize_alerts(alerts)

    def _get_test_documents(self) -> List[Dict[str, Any]]:
        """Documentos de teste para demonstração"""
        return [
            {
                "id": "doc_001",
                "title": "Circular 3.961 - Autenticação de Usuários em Plataformas Financeiras",
                "source": "BCB",
                "document_type": "Circular",
                "url": "https://www.bcb.gov.br/",
                "content": """
                O Banco Central do Brasil determina que todas as instituições de pagamento
                implementem autenticação multifator (MFA) para transações acima de R$ 5.000.
                Prazo de implementação: 180 dias a partir da publicação.
                Afetados: fintechs, instituições de pagamento, gateways de pagamento.
                """
            },
            {
                "id": "doc_002",
                "title": "Instrução CVM 620 - Conformidade com Dados Pessoais",
                "source": "CVM",
                "document_type": "Instrução",
                "url": "https://www.cvm.gov.br/",
                "content": """
                A Comissão de Valores Mobiliários estabelece requisitos para proteção de dados
                pessoais em plataformas de investimento digital. Conformidade com LGPD obrigatória.
                Deadline: 31/12/2024 para plataformas existentes.
                """
            }
        ]

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status atual do sistema"""
        return {
            "status": self.system_status,
            "monitor": self.monitor_agent.get_status(),
            "alerts_generated": self.alert_agent.get_alert_summary(),
            "timestamp": datetime.now().isoformat()
        }

    def mark_alert_reviewed(self, alert_id: str, reviewer_notes: str = "") -> bool:
        """Marca alerta como revisado por humano"""
        # TODO: Implementar atualização em banco de dados
        logger.info(f"Alerta {alert_id} marcado como revisado")
        return True


def main():
    """Função principal para teste"""
    
    # Cria sistema
    system = RegulatoryMonitoringSystem()
    
    # Executa ciclo de monitoramento
    result = system.run_monitoring_cycle()
    
    # Exibe resumo
    print("\n\n" + "=" * 80)
    print("RESUMO DO CICLO")
    print("=" * 80)
    print(f"Documentos coletados: {result['documents_collected']}")
    print(f"Documentos analisados: {result['documents_analyzed']}")
    print(f"Alertas gerados: {result['alerts_generated']}")
    
    if 'summary' in result:
        print(f"\nDistribuição por prioridade:")
        for priority, count in result['summary'].get('by_priority', {}).items():
            print(f"  - {priority}: {count}")
    
    # Exibe status do sistema
    status = system.get_system_status()
    print(f"\nStatus do sistema: {status['status']}")


if __name__ == "__main__":
    main()
