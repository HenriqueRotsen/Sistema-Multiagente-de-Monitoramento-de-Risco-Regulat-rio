"""
Main orchestrator - Coordena os 3 agentes do sistema
"""
from dataclasses import asdict
import argparse
import hashlib
import logging
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

from src.agents.monitor_agent import MonitorAgent
from src.agents.analysis_agent import AnalysisAgent
from src.agents.alert_agent import AlertAgent, StructuredAlert
from src.utils.llm_integration import RegulatoryLLM
from src.utils.data_collection import DocumentRepository

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

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
        if load_dotenv:
            load_dotenv()
        self._configure_logging()

        llm_model = RegulatoryLLM.from_env()
        if llm_model:
            logger.info("LLM configurado: provider=%s model=%s", llm_model.config.provider, llm_model.config.model)
        else:
            logger.info("LLM não configurado; análise usará fallback heurístico")

        db_path = os.getenv("DB_PATH", "regulatory_monitor.db")
        self.repository = DocumentRepository(db_path=db_path)
        self.monitor_agent = MonitorAgent(db_path=db_path)
        self.analysis_agent = AnalysisAgent(llm_model=llm_model)
        self.alert_agent = AlertAgent()
        self.system_status = "initialized"

    def _configure_logging(self):
        """Configura log no console e opcionalmente em arquivo."""
        if logging.getLogger().handlers:
            return

        handlers: List[logging.Handler] = [logging.StreamHandler()]
        log_file = (os.getenv("LOG_FILE", "") or "").strip()
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

        log_level_name = (os.getenv("LOG_LEVEL", "INFO") or "INFO").upper()
        log_level = getattr(logging, log_level_name, logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            handlers=handlers,
        )

    def run_monitoring_cycle(
        self,
        manual_documents: List[Dict[str, Any]] = None,
        limit: int = None,
    ) -> Dict[str, Any]:
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
            "cycle_id": f"cycle-{uuid4().hex[:12]}",
            "started_at": datetime.now().isoformat(),
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
            documents = self._collect_documents(manual_documents, limit=limit)
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
        cycle_result["finished_at"] = datetime.now().isoformat()
        self.repository.save_monitoring_cycle(cycle_result)
        
        return cycle_result

    def _collect_documents(
        self,
        manual_documents: List[Dict[str, Any]] = None,
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Etapa 1: Coleta de documentos
        
        Usa coleta automática dos agentes quando não há documentos manuais.
        """
        if manual_documents:
            logger.info("Usando documentos manuais para teste")
            if limit is not None:
                manual_documents = manual_documents[: max(0, limit)]
            for doc in manual_documents:
                self.repository.add_document(doc)
            return manual_documents
        
        collected = self.monitor_agent.monitor_sources()
        unique_documents = self.monitor_agent.eliminate_duplicates(collected)
        screened_documents = self.monitor_agent.initial_screening(unique_documents)
        if unique_documents and not screened_documents:
            logger.warning(
                "Triagem inicial retornou 0 itens após %s documentos únicos; usando lista sem triagem para evitar ciclo vazio.",
                len(unique_documents),
            )
            screened_documents = unique_documents

        documents_as_dict = [
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
        if limit is not None:
            documents_as_dict = documents_as_dict[: max(0, limit)]

        for doc in documents_as_dict:
            self.repository.add_document(doc)

        if not documents_as_dict:
            pending_limit = limit if limit is not None else 10
            pending_docs = self.repository.get_pending_documents(limit=pending_limit)
            if pending_docs:
                logger.info(
                    "Nenhum documento novo nas fontes; reutilizando %s documentos pendentes do banco.",
                    len(pending_docs),
                )
                return pending_docs

        return documents_as_dict

    def _analyze_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Etapa 2: Análise de impacto regulatório"""
        analyses = []
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"  [{i}/{len(documents)}] Analisando: {doc.get('title', 'sem título')[:60]}...")

            metadata = {
                "id": doc.get("id", f"doc_{i}"),
                "title": doc.get("title", ""),
                "source": doc.get("source", "BCB"),
                "document_type": doc.get("document_type", ""),
                "url": doc.get("url", ""),
                "published_date": doc.get("published_date"),
            }
            content_text = doc.get("content", "")
            content_hash = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
            cached_analysis = self.repository.get_cached_extraction_by_content_hash(content_hash)

            if cached_analysis:
                analysis = dict(cached_analysis)
                analysis["document_id"] = metadata["id"]
                analysis["title"] = metadata["title"]
                analysis["regulatory_body"] = metadata["source"]
                analysis["document_type"] = metadata["document_type"]
                logger.info("    ↳ análise reutilizada do cache por hash")
            else:
                extracted_info = self.analysis_agent.analyze_document(content_text, metadata)
                analysis = asdict(extracted_info)

            analysis["source_url"] = doc.get("url", "")
            analyses.append(analysis)
            document_id = analysis.get("document_id")
            if document_id:
                self.repository.save_extraction(document_id, analysis)
                self.repository.update_processing_status(document_id, "processed")
                self.monitor_agent.update_processed(document_id)
        
        return analyses

    def _generate_alerts(self, analyses: List[Dict[str, Any]]) -> List[StructuredAlert]:
        """Etapa 3: Geração de alertas"""
        alerts = self.alert_agent.batch_generate_alerts(analyses)
        document_map = {(a.get("title"), a.get("source_url")): a.get("document_id") for a in analyses}
        for alert in alerts:
            payload = alert.to_dict()
            document_id = document_map.get((alert.document_title, alert.source_url))
            self.repository.save_alert(document_id=document_id, alert=payload)
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
        doc_stats = self.repository.get_statistics()
        alert_stats = self.repository.get_alert_statistics()
        return {
            "status": self.system_status,
            "monitor": {**self.monitor_agent.get_status(), **doc_stats},
            "alerts_generated": alert_stats,
            "timestamp": datetime.now().isoformat()
        }

    def mark_alert_reviewed(self, alert_id: str, reviewer_notes: str = "") -> bool:
        """Marca alerta como revisado por humano"""
        updated = self.repository.mark_alert_reviewed(alert_id, reviewer_notes)
        if updated:
            logger.info(f"Alerta {alert_id} marcado como revisado")
        return updated

    def archive_alert(self, alert_id: str) -> bool:
        """Arquiva alerta, removendo-o da lista principal de revisão."""
        archived = self.repository.archive_alert(alert_id)
        if archived:
            logger.info(f"Alerta {alert_id} arquivado")
        return archived

    def get_persisted_alerts(
        self, include_reviewed: bool = True, include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """Retorna alertas já persistidos no banco."""
        return self.repository.get_alerts(
            include_reviewed=include_reviewed, include_archived=include_archived
        )

    def get_cycle_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna histórico de ciclos persistidos."""
        return self.repository.get_monitoring_cycles(limit=limit)

    def export_alerts(self, alerts: List[Dict[str, Any]], format: str = "json") -> str:
        """Exporta lista de alertas persistidos em múltiplos formatos."""
        return self.alert_agent.export_alert_dicts(alerts=alerts, format=format)

    def export_cycle_report(self, cycle_result: Dict[str, Any], format: str = "json") -> str:
        """Exporta relatório consolidado de um ciclo específico."""
        return self.alert_agent.export_cycle_report(cycle_result=cycle_result, format=format)


def main():
    """Função principal para teste"""
    parser = argparse.ArgumentParser(description="Sistema de monitoramento regulatório")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita a quantidade de documentos coletados/analisados no ciclo.",
    )
    args = parser.parse_args()
    
    # Cria sistema
    system = RegulatoryMonitoringSystem()
    
    # Executa ciclo de monitoramento
    result = system.run_monitoring_cycle(limit=args.limit)
    
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
