"""
Monitor Agent - Monitora fontes regulatórias e identifica novos documentos
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
import hashlib
import json
import logging
import os
import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET

try:
    import feedparser
except ImportError:  # pragma: no cover - exercised when dependencies are not installed
    feedparser = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - fallback keeps CLI usable before pip install
    BeautifulSoup = None

logger = logging.getLogger(__name__)


BCB_RSS_FEED = "https://www.bcb.gov.br/htms/novidades/ult_noticias.xml"
BCB_NEWS_API = "https://www.bcb.gov.br/api/servico/sitebcb/noticias?quantidade=20"


@dataclass
class RegulatoryDocument:
    """Representa um documento regulatório"""
    id: str
    title: str
    source: str  # "BCB", "CVM"
    document_type: str  # "Circular", "Resolução", "Ofício", etc
    published_date: datetime
    url: str
    content: str
    metadata: Dict[str, Any] = None
    processed: bool = False
    relevance_score: float = 0.0


class MonitorAgent:
    """
    Agente responsável por:
    1. Monitorar fontes regulatórias (BCB, CVM)
    2. Identificar novos documentos
    3. Triagem inicial e eliminação de duplicatas
    4. Encaminhar para análise
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.processed_docs = set()
        self.sources = {
            "BCB": os.getenv("BCB_NEWS_API_URL") or os.getenv("BCB_RSS_URL", BCB_NEWS_API),
            "CVM": "https://www.cvm.gov.br/"
        }

    def monitor_sources(self) -> List[RegulatoryDocument]:
        """
        Monitora todas as fontes configuradas
        Retorna lista de novos documentos encontrados
        """
        new_documents = []
        
        logger.info("Iniciando monitoramento de fontes regulatórias...")
        
        for source_name, source_url in self.sources.items():
            logger.info(f"Coletando documentos de {source_name}...")
            docs = self._fetch_from_source(source_name, source_url)
            
            # Filtrar duplicatas
            filtered_docs = [d for d in docs if d.id not in self.processed_docs]
            new_documents.extend(filtered_docs)
            
            logger.info(f"Found {len(filtered_docs)} new documents from {source_name}")
        
        return new_documents

    def _fetch_from_source(self, source_name: str, source_url: str) -> List[RegulatoryDocument]:
        """
        Busca documentos de uma fonte específica
        
        TODO:
        - Implementar coleta de RSS do BCB
        - Implementar scraping do portal CVM
        - Implementar tratamento de APIs públicas
        - Normalizar metadados entre fontes
        """
        documents = []
        
        try:
            if source_name == "BCB":
                documents = self._fetch_bcb_documents(source_url)
            elif source_name == "CVM":
                documents = self._fetch_cvm_documents(source_url)
        except Exception as e:
            logger.error(f"Erro ao coletar de {source_name}: {str(e)}")
        
        return documents

    def _fetch_bcb_documents(self, url: str) -> List[RegulatoryDocument]:
        """
        Coleta documentos regulatórios do BCB via API pública ou RSS.

        A API de notícias do BCB contém publicações variadas, então esta etapa
        filtra itens com sinais de atos normativos antes de convertê-los para o
        formato comum do sistema.
        """
        source_url = url or BCB_NEWS_API
        documents = []
        for entry in self._parse_bcb_entries(source_url):
            title = self._clean_html(entry.get("title", ""))
            summary = self._clean_html(
                entry.get("summary")
                or entry.get("description")
                or self._entry_content(entry)
            )
            document_type = self._detect_bcb_document_type(title, summary)

            if not document_type:
                continue

            published_date = self._parse_entry_date(entry) or datetime.now()
            link = entry.get("link", "")
            doc_id = self._build_document_id("BCB", title, link, published_date)

            documents.append(
                RegulatoryDocument(
                    id=doc_id,
                    title=title,
                    source="BCB",
                    document_type=document_type,
                    published_date=published_date,
                    url=link,
                    content=summary or title,
                    metadata={
                        "feed_url": source_url,
                        "raw_id": entry.get("id") or entry.get("guid", ""),
                        "collected_at": datetime.now().isoformat(),
                        "published_raw": entry.get("published", ""),
                    },
                )
            )

        logger.info("Coletados %s documentos regulatórios do BCB", len(documents))
        return documents

    def _fetch_cvm_documents(self, url: str) -> List[RegulatoryDocument]:
        """
        TODO: Implementar coleta CVM
        - Portal: https://www.cvm.gov.br/
        - Tipos: Instruções, Resoluções, Deliberações, Comunicados
        - Scraping ou API se disponível
        """
        return []

    def _detect_bcb_document_type(self, title: str, summary: str = "") -> Optional[str]:
        """Detecta tipo normativo em itens do RSS do BCB."""
        text = f"{title} {summary}".lower()
        patterns = [
            (r"\bresolu[cç][aã]o\s+conjunta\b", "Resolução Conjunta"),
            (r"\bresolu[cç][aã]o\s+bcb\b|\bresolu[cç][aã]o\b", "Resolução"),
            (r"\bcarta\s+circular\b", "Carta Circular"),
            (r"\bcircular\b", "Circular"),
            (r"\binstru[cç][aã]o\s+normativa\b", "Instrução Normativa"),
            (r"\bcomunicado\b", "Comunicado"),
            (r"\bof[ií]cio\b", "Ofício"),
            (r"\bconsulta\s+p[uú]blica\b", "Consulta Pública"),
            (r"\bedital\b", "Edital"),
        ]

        for pattern, document_type in patterns:
            if re.search(pattern, text):
                return document_type

        return None

    def _parse_bcb_entries(self, source_url: str) -> List[Dict[str, Any]]:
        """Seleciona parser conforme fonte configurada para o BCB."""
        if source_url.endswith(".xml"):
            return self._parse_rss_entries(source_url)
        return self._parse_bcb_news_api(source_url)

    def _parse_bcb_news_api(self, api_url: str) -> List[Dict[str, Any]]:
        """Parseia a API pública de notícias do site atual do BCB."""
        with urlopen(api_url, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))

        entries = []
        for item in payload.get("conteudo", []):
            item_id = item.get("Id", "")
            entries.append(
                {
                    "title": item.get("titulo", ""),
                    "summary": " ".join(
                        value
                        for value in [item.get("lead", ""), item.get("corpo", "")]
                        if value
                    ),
                    "link": self._build_bcb_news_url(item_id),
                    "published": item.get("dataPublicacao", ""),
                    "updated": item.get("ultimaAtualizacao", ""),
                    "id": str(item_id),
                }
            )
        return entries

    def _parse_rss_entries(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parseia RSS com feedparser quando disponível, ou XML padrão."""
        if feedparser:
            feed = feedparser.parse(feed_url)
            if getattr(feed, "bozo", False):
                logger.warning("Feed BCB retornou aviso de parsing: %s", feed.get("bozo_exception"))
            return list(feed.entries)

        with urlopen(feed_url, timeout=15) as response:
            raw_xml = response.read()

        root = ET.fromstring(raw_xml)
        entries = []
        for item in root.findall(".//item"):
            entries.append(
                {
                    "title": self._xml_child_text(item, "title"),
                    "summary": self._xml_child_text(item, "description"),
                    "link": self._xml_child_text(item, "link"),
                    "published": self._xml_child_text(item, "pubDate"),
                    "id": self._xml_child_text(item, "guid"),
                }
            )
        return entries

    def _build_bcb_news_url(self, item_id: Any) -> str:
        """Monta URL pública de detalhe da notícia no site do BCB."""
        if not item_id:
            return "https://www.bcb.gov.br/"
        return f"https://www.bcb.gov.br/detalhenoticia/{item_id}/noticia"

    def _xml_child_text(self, item: ET.Element, tag: str) -> str:
        """Lê texto de um filho XML ignorando namespaces simples."""
        child = item.find(tag)
        if child is not None and child.text:
            return child.text

        for candidate in item:
            if candidate.tag.endswith(f"}}{tag}") and candidate.text:
                return candidate.text

        return ""

    def _parse_entry_date(self, entry: Dict[str, Any]) -> Optional[datetime]:
        """Normaliza datas vindas do feed RSS."""
        for parsed_field in ("published_parsed", "updated_parsed"):
            parsed_value = entry.get(parsed_field)
            if parsed_value:
                return datetime(*parsed_value[:6])

        for text_field in ("published", "updated", "created"):
            value = entry.get(text_field)
            if not value:
                continue
            try:
                if isinstance(value, str) and "T" in value:
                    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
                parsed = parsedate_to_datetime(value)
                return parsed.replace(tzinfo=None)
            except (TypeError, ValueError, IndexError):
                logger.debug("Não foi possível parsear data do BCB: %s", value)

        return None

    def _build_document_id(self, source: str, title: str, url: str, published_date: datetime) -> str:
        """Cria identificador estável quando o RSS não fornece GUID confiável."""
        raw = f"{source}|{title}|{url}|{published_date.date().isoformat()}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"{source.lower()}-{digest}"

    def _entry_content(self, entry: Dict[str, Any]) -> str:
        """Extrai conteúdo textual de entradas RSS com campo content."""
        content = entry.get("content")
        if isinstance(content, list) and content:
            return content[0].get("value", "")
        return ""

    def _clean_html(self, text: str) -> str:
        """Remove tags HTML e normaliza espaços."""
        if not text:
            return ""
        if "<" not in text and ">" not in text:
            return " ".join(unescape(text).split())
        if BeautifulSoup:
            return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
        return " ".join(re.sub(r"<[^>]+>", " ", unescape(text)).split())

    def eliminate_duplicates(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """
        Elimina documentos duplicados por:
        - Hash de conteúdo
        - URL
        - Título + data
        """
        unique_docs = []
        seen = set()
        
        for doc in documents:
            doc_hash = hash((doc.title, doc.source, doc.published_date.date()))
            if doc_hash not in seen:
                unique_docs.append(doc)
                seen.add(doc_hash)
        
        return unique_docs

    def initial_screening(self, documents: List[RegulatoryDocument]) -> List[RegulatoryDocument]:
        """
        Triagem inicial baseada em:
        - Tipo de documento (excluir newsletters, notícias genéricas)
        - Palavras-chave regulatórias
        - Metadata estrutura
        """
        screened = []
        
        regulatory_keywords = [
            "circular", "resolução", "ofício", "comunicado",
            "instrução", "deliberação", "normativo", "resolução conjunta"
        ]
        
        for doc in documents:
            doc_type_lower = doc.document_type.lower()
            if any(keyword in doc_type_lower for keyword in regulatory_keywords):
                screened.append(doc)
        
        return screened

    def update_processed(self, doc_id: str):
        """Marca documento como processado"""
        self.processed_docs.add(doc_id)

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do monitor"""
        return {
            "total_processed": len(self.processed_docs),
            "sources": list(self.sources.keys()),
            "last_update": datetime.now().isoformat()
        }
