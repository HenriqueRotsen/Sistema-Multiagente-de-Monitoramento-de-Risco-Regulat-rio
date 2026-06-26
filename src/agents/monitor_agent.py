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
import time
from urllib.parse import urljoin
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from src.utils.data_collection import DocumentRepository

try:
    import feedparser
except ImportError:  # pragma: no cover - exercised when dependencies are not installed
    feedparser = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - fallback keeps CLI usable before pip install
    BeautifulSoup = None

logger = logging.getLogger(__name__)


BCB_NEWS_API = "https://www.bcb.gov.br/api/servico/sitebcb/noticias?quantidade=20"
CVM_LEGISLATION_URL = "https://conteudo.cvm.gov.br/legislacao/index.html?buscado=true&contCategoriasChec="


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
        self.db_path = db_path or os.getenv("DB_PATH", "regulatory_monitor.db")
        self.repository = DocumentRepository(self.db_path)
        self.processed_docs = set()
        self.sources = {
            "BCB": os.getenv("BCB_NEWS_API_URL") or os.getenv("BCB_RSS_URL", BCB_NEWS_API),
            "CVM": os.getenv("CVM_LEGISLATION_URL", CVM_LEGISLATION_URL),
        }
        self.retry_attempts = max(0, int(os.getenv("SOURCE_RETRY_ATTEMPTS", "2")))
        self.retry_backoff_seconds = float(os.getenv("SOURCE_RETRY_BACKOFF_SECONDS", "1.0"))
        self.bcb_timeout_seconds = int(os.getenv("BCB_TIMEOUT_SECONDS", "15"))
        self.cvm_timeout_seconds = int(os.getenv("CVM_TIMEOUT_SECONDS", "20"))

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
            filtered_docs = []
            for doc in docs:
                if doc.id in self.processed_docs:
                    continue
                if self.repository.check_duplicate(
                    url=doc.url,
                    doc_id=doc.id,
                    content_hash=self._content_hash(doc.content),
                    title=doc.title,
                    source=doc.source,
                    published_date=doc.published_date,
                ):
                    continue
                filtered_docs.append(doc)
            new_documents.extend(filtered_docs)
            
            logger.info(f"Found {len(filtered_docs)} new documents from {source_name}")
        
        return new_documents

    def _fetch_from_source(self, source_name: str, source_url: str) -> List[RegulatoryDocument]:
        """
        Busca documentos de uma fonte específica

        O BCB ja usa a API publica atual, com suporte opcional a RSS/XML
        legado quando configurado. A CVM ainda e uma pendencia.
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
        Coleta documentos da CVM pela página oficial de legislação.

        Estratégia:
        - Ler listagem da CVM e extrair blocos com título, tipo e data
        - Filtrar apenas atos regulatórios relevantes ao monitor
        - Seguir paginação por algumas páginas para capturar histórico recente
        """
        base_url = url or CVM_LEGISLATION_URL
        max_pages = max(1, int(os.getenv("CVM_MAX_PAGES", "2")))
        documents: List[RegulatoryDocument] = []
        visited_pages = set()
        next_page_url = base_url

        for _ in range(max_pages):
            if not next_page_url or next_page_url in visited_pages:
                break
            visited_pages.add(next_page_url)

            entries, candidate_next_page = self._parse_cvm_legislation_page(next_page_url)
            for entry in entries:
                title = self._clean_html(entry.get("title", ""))
                summary = self._clean_html(entry.get("summary", ""))
                document_type = self._normalize_cvm_document_type(
                    entry.get("document_type", ""),
                    title,
                    summary,
                )
                if not document_type:
                    continue

                published_date = self._parse_cvm_date(entry.get("published", "")) or datetime.now()
                source_link = entry.get("link", "") or next_page_url
                doc_id = self._build_document_id("CVM", title, source_link, published_date)
                documents.append(
                    RegulatoryDocument(
                        id=doc_id,
                        title=title,
                        source="CVM",
                        document_type=document_type,
                        published_date=published_date,
                        url=source_link,
                        content=summary or title,
                        metadata={
                            "feed_url": next_page_url,
                            "raw_type": entry.get("document_type", ""),
                            "published_raw": entry.get("published", ""),
                            "collected_at": datetime.now().isoformat(),
                        },
                    )
                )

            next_page_url = candidate_next_page

        logger.info("Coletados %s documentos regulatórios da CVM", len(documents))
        return documents

    def _parse_cvm_legislation_page(self, page_url: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Parseia uma página da legislação da CVM e retorna entradas + próxima página."""
        with self._open_url_with_retry(page_url, timeout=self.cvm_timeout_seconds) as response:
            raw_html = response.read().decode("utf-8", errors="ignore")

        if not BeautifulSoup:
            return self._parse_cvm_from_text(raw_html, page_url), None

        soup = BeautifulSoup(raw_html, "html.parser")
        lines = [
            " ".join(text.split())
            for text in soup.get_text("\n", strip=True).splitlines()
            if text and text.strip()
        ]

        title_links = {}
        for anchor in soup.find_all("a", href=True):
            anchor_text = " ".join(anchor.get_text(" ", strip=True).split())
            if anchor_text and anchor_text not in title_links:
                title_links[anchor_text] = urljoin(page_url, anchor["href"])

        entries = self._extract_cvm_entries_from_lines(lines, page_url, title_links)
        return entries, self._extract_cvm_next_page(soup, page_url)

    def _parse_cvm_from_text(self, raw_text: str, page_url: str) -> List[Dict[str, Any]]:
        """Fallback simples sem BeautifulSoup, operando sobre texto cru."""
        lines = [
            " ".join(text.split())
            for text in raw_text.splitlines()
            if text and text.strip()
        ]
        return self._extract_cvm_entries_from_lines(lines, page_url, {})

    def _extract_cvm_entries_from_lines(
        self,
        lines: List[str],
        page_url: str,
        title_links: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """Extrai blocos de entradas da legislação a partir de linhas de texto."""
        entries: List[Dict[str, Any]] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if not self._looks_like_cvm_title(line):
                i += 1
                continue

            title = line
            j = i + 1
            if j < len(lines) and lines[j] == title:
                j += 1

            summary_parts: List[str] = []
            published = ""
            document_type = ""
            while j < len(lines):
                current = lines[j]
                if self._looks_like_cvm_title(current):
                    break
                if current.startswith("Data:"):
                    published = current.replace("Data:", "", 1).strip()
                elif current.startswith("Tipo:"):
                    document_type = current.replace("Tipo:", "", 1).strip()
                elif current.startswith("Tag:") or current in {
                    "Primeira",
                    "Anterior",
                    "Próxima",
                    "Última",
                    "Voltar ao topo",
                }:
                    pass
                elif current.startswith("Páginas ") or current.startswith("Ir para a página"):
                    pass
                elif current.startswith("Itens por página") or current.startswith("Ordenar por"):
                    pass
                else:
                    summary_parts.append(current)
                j += 1

            if document_type or self._normalize_cvm_document_type("", title, " ".join(summary_parts)):
                entries.append(
                    {
                        "title": title,
                        "summary": " ".join(summary_parts).strip(),
                        "document_type": document_type,
                        "published": published,
                        "link": title_links.get(title, page_url),
                    }
                )
            i = j

        return entries

    def _looks_like_cvm_title(self, text: str) -> bool:
        """Heurística para identificar títulos de atos da CVM."""
        normalized = text.lower()
        patterns = [
            r"^resolu[cç][aã]o\s+cvm\b",
            r"^delibera[cç][aã]o\s+cvm\b",
            r"^of[ií]cio\s+circular\s+cvm\b",
            r"^instru[cç][aã]o\s+cvm\b",
            r"^comunicado\b",
            r"^decis[aã]o\s+conjunta\b",
        ]
        return any(re.search(pattern, normalized) for pattern in patterns)

    def _extract_cvm_next_page(self, soup: Any, page_url: str) -> Optional[str]:
        """Encontra URL da próxima página da listagem da CVM."""
        for anchor in soup.find_all("a", href=True):
            text = " ".join(anchor.get_text(" ", strip=True).split()).lower()
            if "próxima" in text or "proxima" in text:
                return urljoin(page_url, anchor["href"])
        return None

    def _normalize_cvm_document_type(self, type_hint: str, title: str, summary: str = "") -> Optional[str]:
        """Normaliza tipos da CVM para o conjunto usado no sistema."""
        candidate = f"{type_hint} {title} {summary}".lower()
        mappings = [
            (r"\bresolu[cç][aã]o\b", "Resolução"),
            (r"\bdelibera[cç][aã]o\b", "Deliberação"),
            (r"\binstru[cç][aã]o\b", "Instrução"),
            (r"\bof[ií]cio\s+circular\b|\bof[ií]cio\b", "Ofício Circular"),
            (r"\bcomunicado\b", "Comunicado"),
            (r"\bdecis[aã]o\s+conjunta\b", "Decisão Conjunta"),
        ]
        for pattern, normalized in mappings:
            if re.search(pattern, candidate):
                return normalized
        return None

    def _parse_cvm_date(self, date_text: str) -> Optional[datetime]:
        """Converte datas da CVM no padrão brasileiro dd/mm/aaaa."""
        if not date_text:
            return None
        try:
            return datetime.strptime(date_text.strip(), "%d/%m/%Y")
        except ValueError:
            logger.debug("Não foi possível parsear data da CVM: %s", date_text)
            return None

    def _open_url_with_retry(self, url: str, timeout: int):
        """Abre URL com retry e backoff exponencial para fontes regulatórias."""
        last_exception: Optional[Exception] = None
        for attempt in range(self.retry_attempts + 1):
            try:
                return urlopen(url, timeout=timeout)
            except (URLError, HTTPError, TimeoutError, OSError) as exc:
                last_exception = exc
                if attempt >= self.retry_attempts:
                    break
                backoff = self.retry_backoff_seconds * (2 ** attempt)
                logger.warning(
                    "Falha ao acessar %s (tentativa %s/%s). Retry em %.1fs: %s",
                    url,
                    attempt + 1,
                    self.retry_attempts + 1,
                    backoff,
                    str(exc),
                )
                time.sleep(backoff)
        raise RuntimeError(f"Não foi possível acessar URL {url}: {last_exception}")

    def _detect_bcb_document_type(self, title: str, summary: str = "") -> Optional[str]:
        """Detecta tipo normativo em entradas do BCB."""
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
        with self._open_url_with_retry(api_url, timeout=self.bcb_timeout_seconds) as response:
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

        with self._open_url_with_retry(feed_url, timeout=self.bcb_timeout_seconds) as response:
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
        """Normaliza datas vindas da API ou de feed RSS."""
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
        """Cria identificador estável quando a fonte não fornece GUID confiável."""
        raw = f"{source}|{title}|{url}|{published_date.date().isoformat()}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"{source.lower()}-{digest}"

    def _content_hash(self, content: str) -> str:
        """Gera hash estável do conteúdo para deduplicação."""
        return hashlib.sha256((content or "").encode("utf-8")).hexdigest()

    def _entry_content(self, entry: Dict[str, Any]) -> str:
        """Extrai conteúdo textual de entradas com campo content."""
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
        if not doc_id:
            return
        self.processed_docs.add(doc_id)
        self.repository.update_processing_status(doc_id, "processed")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do monitor"""
        return {
            "total_processed": len(self.processed_docs),
            "sources": list(self.sources.keys()),
            "last_update": datetime.now().isoformat()
        }
