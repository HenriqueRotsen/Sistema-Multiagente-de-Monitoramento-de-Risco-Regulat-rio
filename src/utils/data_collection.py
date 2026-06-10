"""
Utilitários para coleta e processamento de dados regulatórios.

O pipeline principal usa `src/agents/monitor_agent.py`. Este módulo mantém
funções auxiliares e o esqueleto do repositório persistente que será evoluído
no próximo passo.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from html import unescape
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DataCollector:
    """Coleta documentos de fontes regulatórias"""

    # URLs principais
    BCB_NEWS_API = "https://www.bcb.gov.br/api/servico/sitebcb/noticias?quantidade=20"
    BCB_BASE_URL = "https://www.bcb.gov.br"
    CVM_BASE_URL = "https://www.cvm.gov.br"

    @staticmethod
    def fetch_bcb_news() -> List[Dict[str, Any]]:
        """
        Coleta publicações recentes do BCB pela API pública atual.

        Para a coleta usada no sistema, prefira MonitorAgent, que também
        normaliza para RegulatoryDocument e filtra itens regulatórios.
        """
        try:
            response = requests.get(DataCollector.BCB_NEWS_API, timeout=15)
            response.raise_for_status()
            payload = response.json()
            documents = []

            for entry in payload.get("conteudo", []):
                item_id = entry.get("Id", "")
                doc = {
                    'title': DataCollector._clean_html(entry.get('titulo', '')),
                    'published': entry.get('dataPublicacao', ''),
                    'link': f"{DataCollector.BCB_BASE_URL}/detalhenoticia/{item_id}/noticia" if item_id else DataCollector.BCB_BASE_URL,
                    'summary': DataCollector._clean_html(
                        " ".join(
                            value
                            for value in [entry.get('lead', ''), entry.get('corpo', '')]
                            if value
                        )
                    ),
                    'source': 'BCB'
                }
                documents.append(doc)

            logger.info(f"Coletadas {len(documents)} publicações do BCB")
            return documents

        except Exception as e:
            logger.error(f"Erro ao coletar publicações do BCB: {str(e)}")
            return []

    @staticmethod
    def fetch_bcb_rss() -> List[Dict[str, Any]]:
        """
        Compatibilidade para chamadas antigas.

        O RSS historico do BCB nao e mais o caminho padrao do projeto; esta
        funcao delega para a API atual.
        """
        return DataCollector.fetch_bcb_news()

    @staticmethod
    def fetch_bcb_circulares() -> List[Dict[str, Any]]:
        """
        Pendente: implementar coleta de atos normativos detalhados do BCB.
        
        URL: https://www.bcb.gov.br/content/cns/atos/
        - Listar circulares por ano
        - Extrair título, número, data
        - Link para PDF
        """
        return []

    @staticmethod
    def fetch_cvm_documents() -> List[Dict[str, Any]]:
        """
        Pendente: implementar coleta de documentos CVM.
        
        CVM oferece múltiplas páginas:
        - Instruções: https://www.cvm.gov.br/decisoes/instrucoes
        - Resoluções: https://www.cvm.gov.br/decisoes/resolucoes
        - Deliberações: https://www.cvm.gov.br/decisoes/deliberacoes
        
        Necessário:
        - Scraping ou API
        - Normalizar tipos
        - Extrair metadados (data, número, tema)
        """
        return []

    @staticmethod
    def validate_document(doc: Dict[str, Any]) -> bool:
        """Valida se documento tem campos obrigatórios"""
        required = ['title', 'published', 'source', 'link']
        return all(field in doc for field in required)

    @staticmethod
    def normalize_date(date_str: str) -> Optional[datetime]:
        """
        Normaliza datas simples.

        Pendencias:
        - Suportar múltiplos formatos
        - Lidar com descrições vagas ("em breve", "30 dias após publicação")
        - Retornar datetime ou None
        """
        formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d de %B de %Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Não conseguiu normalizar data: {date_str}")
        return None

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove tags HTML e normaliza espaços."""
        if not text:
            return ""
        if "<" in text and ">" in text:
            text = BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        return " ".join(unescape(text).split())


class TextProcessor:
    """Processa e limpa texto regulatório"""

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove caracteres especiais e normaliza espaçamento"""
        # Remove quebras de linha e espaços múltiplos
        text = ' '.join(text.split())
        # Remove caracteres especiais mantendo pontuação
        text = text.replace('\xa0', ' ')
        return text

    @staticmethod
    def extract_sections(text: str) -> Dict[str, str]:
        """
        Pendente: implementar extração de seções de documento legal.
        
        Documentos regulatórios tem estrutura:
        - Cabeçalho (regulador, tipo, número)
        - Preâmbulo (justificativa)
        - Artigos (obrigações)
        - Considerandos (motivos)
        - Vigência (quando entra em vigor)
        - Assinatura
        
        Extrair cada seção para processamento posterior
        """
        return {}

    @staticmethod
    def extract_dates(text: str) -> List[Dict[str, Any]]:
        """
        Pendente: implementar extração utilitária de datas e prazos.
        
        Padrões a procurar:
        - "30 de janeiro de 2024"
        - "31.12.2024"
        - "até 30 dias após publicação"
        - "vigência imediata"
        - "A partir de 01.01.2025"
        """
        return []

    @staticmethod
    def extract_obligations(text: str) -> List[str]:
        """
        Pendente: implementar extração utilitária de obrigações.
        
        Procurar por verbos modal + obrigação:
        - "As instituições deverão..."
        - "É obrigado a..."
        - "Fica determinado que..."
        - "Será aplicada..."
        
        Estruturar como lista de obrigações
        """
        return []

    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """
        Pendente: implementar NER para identificar entidades.
        
        Tipos de entidades:
        - Instituições financeiras
        - Reguladores
        - Tipos de produto/serviço
        - Jurisdições
        """
        return []


class DocumentRepository:
    """Gerencia histórico de documentos processados"""

    def __init__(self, db_path: str = "regulatory_monitor.db"):
        """
        Pendente: implementar persistência em banco de dados.
        
        Schema necessário:
        - documents: id, title, source, url, content_hash, published_date, processed_date, processed
        - extractions: document_id, extracted_data_json, confidence_score
        - alerts: document_id, alert_id, priority, human_reviewed
        """
        self.db_path = db_path

    def add_document(self, doc: Dict[str, Any]) -> bool:
        """Adiciona documento ao repositório"""
        # Pendente: implementar inserção em banco
        return True

    def check_duplicate(self, url: str) -> bool:
        """Verifica se documento já foi processado"""
        # Pendente: implementar query no banco
        return False

    def get_processed_documents(self) -> List[Dict[str, Any]]:
        """Retorna documentos já processados"""
        # Pendente: implementar query
        return []

    def update_processing_status(self, doc_id: str, status: str) -> bool:
        """Atualiza status de processamento"""
        # Pendente: implementar update
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de processamento"""
        return {
            "total_documents": 0,
            "processed": 0,
            "pending": 0,
            "by_source": {},
            "last_update": None
        }
