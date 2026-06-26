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
import hashlib
import json
from pathlib import Path
import sqlite3
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
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _init_db(self):
        schema_path = Path(__file__).resolve().parents[2] / "database" / "schema.sql"
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
        else:
            schema_sql = self._fallback_schema()

        with self._get_connection() as conn:
            conn.executescript(schema_sql)

    def _fallback_schema(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            document_type TEXT,
            url TEXT NOT NULL UNIQUE,
            content_hash TEXT,
            content TEXT,
            published_date TEXT,
            metadata_json TEXT,
            collected_at TEXT NOT NULL,
            processed INTEGER NOT NULL DEFAULT 0,
            processed_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
        CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
        CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);

        CREATE TABLE IF NOT EXISTS extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            extracted_data_json TEXT NOT NULL,
            confidence_score REAL,
            extraction_method TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_extractions_document ON extractions(document_id);

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            document_id TEXT,
            priority TEXT NOT NULL,
            human_reviewed INTEGER NOT NULL DEFAULT 0,
            reviewer_notes TEXT,
            alert_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_alerts_reviewed ON alerts(human_reviewed);
        CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);

        CREATE TABLE IF NOT EXISTS monitoring_cycles (
            cycle_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            documents_collected INTEGER NOT NULL DEFAULT 0,
            documents_analyzed INTEGER NOT NULL DEFAULT 0,
            alerts_generated INTEGER NOT NULL DEFAULT 0,
            errors_json TEXT NOT NULL DEFAULT "[]",
            summary_json TEXT NOT NULL DEFAULT "{}"
        );

        CREATE INDEX IF NOT EXISTS idx_cycles_finished_at ON monitoring_cycles(finished_at);
        """

    def _to_iso(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256((content or "").encode("utf-8")).hexdigest()

    def add_document(self, doc: Dict[str, Any]) -> bool:
        """Adiciona documento ao repositório"""
        doc_id = doc.get("id")
        if not doc_id:
            logger.warning("Documento sem id não pode ser persistido")
            return False

        payload = (
            doc_id,
            doc.get("title", ""),
            doc.get("source", ""),
            doc.get("document_type", ""),
            doc.get("url", ""),
            self._content_hash(doc.get("content", "")),
            doc.get("content", ""),
            self._to_iso(doc.get("published_date")),
            json.dumps(doc.get("metadata", {}), ensure_ascii=False),
            datetime.now().isoformat(),
            1 if doc.get("processed") else 0,
            datetime.now().isoformat() if doc.get("processed") else None,
        )

        query = """
            INSERT OR IGNORE INTO documents (
                id, title, source, document_type, url, content_hash, content,
                published_date, metadata_json, collected_at, processed, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.execute(query, payload)
            return cursor.rowcount > 0

    def check_duplicate(
        self,
        url: str = "",
        doc_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        title: Optional[str] = None,
        source: Optional[str] = None,
        published_date: Optional[Any] = None,
    ) -> bool:
        """Verifica se documento já foi processado"""
        clauses = []
        params: List[Any] = []

        if doc_id:
            clauses.append("id = ?")
            params.append(doc_id)
        if url:
            clauses.append("url = ?")
            params.append(url)
        if content_hash:
            clauses.append("content_hash = ?")
            params.append(content_hash)
        if title and source and published_date:
            clauses.append("(title = ? AND source = ? AND published_date = ?)")
            params.extend([title, source, self._to_iso(published_date)])

        if not clauses:
            return False

        query = f"SELECT 1 FROM documents WHERE {' OR '.join(clauses)} LIMIT 1"
        with self._get_connection() as conn:
            row = conn.execute(query, params).fetchone()
            return row is not None

    def get_document_id_by_url(self, url: str) -> Optional[str]:
        """Retorna id de documento com base na URL."""
        if not url:
            return None
        with self._get_connection() as conn:
            row = conn.execute("SELECT id FROM documents WHERE url = ? LIMIT 1", (url,)).fetchone()
            return row["id"] if row else None

    def ensure_document_stub(self, doc_id: str):
        """Cria stub mínimo quando análise chega sem documento persistido."""
        if not doc_id:
            return
        with self._get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM documents WHERE id = ? LIMIT 1",
                (doc_id,),
            ).fetchone()
            if exists:
                return
            conn.execute(
                """
                INSERT INTO documents (
                    id, title, source, document_type, url, content_hash, content,
                    published_date, metadata_json, collected_at, processed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    "Documento manual",
                    "MANUAL",
                    "",
                    f"manual://{doc_id}",
                    self._content_hash(doc_id),
                    "",
                    None,
                    "{}",
                    datetime.now().isoformat(),
                    0,
                ),
            )

    def save_extraction(self, document_id: str, extraction: Dict[str, Any]) -> bool:
        """Salva resultado de análise estruturada."""
        if not document_id:
            return False

        self.ensure_document_stub(document_id)
        confidence_scores = extraction.get("confidence_scores", {})
        confidence_mean = None
        if confidence_scores:
            confidence_mean = sum(confidence_scores.values()) / len(confidence_scores)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO extractions (document_id, extracted_data_json, confidence_score, extraction_method, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    json.dumps(extraction, ensure_ascii=False, default=str),
                    confidence_mean,
                    extraction.get("extraction_method"),
                    datetime.now().isoformat(),
                ),
            )
        return True

    def get_cached_extraction_by_content_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Retorna extração mais recente para um hash de conteúdo já processado."""
        if not content_hash:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT e.extracted_data_json
                FROM extractions e
                JOIN documents d ON d.id = e.document_id
                WHERE d.content_hash = ?
                ORDER BY datetime(e.created_at) DESC
                LIMIT 1
                """,
                (content_hash,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["extracted_data_json"])

    def save_alert(self, document_id: Optional[str], alert: Dict[str, Any]) -> bool:
        """Salva alerta gerado para histórico e interface."""
        alert_id = alert.get("alert_id")
        if not alert_id:
            return False

        if document_id:
            self.ensure_document_stub(document_id)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO alerts (
                    alert_id, document_id, priority, human_reviewed, reviewer_notes,
                    alert_json, created_at, reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    document_id,
                    alert.get("priority", "BAIXO"),
                    1 if alert.get("human_reviewed") else 0,
                    alert.get("reviewer_notes", ""),
                    json.dumps(alert, ensure_ascii=False, default=str),
                    alert.get("created_at") or datetime.now().isoformat(),
                    alert.get("reviewed_at"),
                ),
            )
        return True

    def mark_alert_reviewed(self, alert_id: str, reviewer_notes: str = "") -> bool:
        """Marca alerta como revisado."""
        reviewed_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT alert_json FROM alerts WHERE alert_id = ? LIMIT 1",
                (alert_id,),
            ).fetchone()
            if not row:
                return False

            payload = json.loads(row["alert_json"])
            payload["human_reviewed"] = True
            payload["reviewer_notes"] = reviewer_notes
            payload["reviewed_at"] = reviewed_at

            cursor = conn.execute(
                """
                UPDATE alerts
                SET human_reviewed = 1, reviewer_notes = ?, reviewed_at = ?, alert_json = ?
                WHERE alert_id = ?
                """,
                (
                    reviewer_notes,
                    reviewed_at,
                    json.dumps(payload, ensure_ascii=False, default=str),
                    alert_id,
                ),
            )
            return cursor.rowcount > 0

    def get_alerts(self, include_reviewed: bool = True) -> List[Dict[str, Any]]:
        """Retorna alertas persistidos ordenados por data."""
        where_clause = "" if include_reviewed else "WHERE human_reviewed = 0"
        query = f"""
            SELECT alert_json
            FROM alerts
            {where_clause}
            ORDER BY datetime(created_at) DESC
        """
        with self._get_connection() as conn:
            rows = conn.execute(query).fetchall()
        return [json.loads(row["alert_json"]) for row in rows]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de alertas."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS c FROM alerts").fetchone()["c"]
            reviewed = conn.execute("SELECT COUNT(*) AS c FROM alerts WHERE human_reviewed = 1").fetchone()["c"]
            by_priority_rows = conn.execute(
                "SELECT priority, COUNT(*) AS c FROM alerts GROUP BY priority"
            ).fetchall()
        return {
            "total": total,
            "reviewed": reviewed,
            "pending_review": total - reviewed,
            "by_priority": {row["priority"]: row["c"] for row in by_priority_rows},
        }

    def save_monitoring_cycle(self, cycle_result: Dict[str, Any]) -> bool:
        """Persiste resumo de execução de ciclo de monitoramento."""
        cycle_id = cycle_result.get("cycle_id")
        if not cycle_id:
            return False
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO monitoring_cycles (
                    cycle_id, started_at, finished_at,
                    documents_collected, documents_analyzed, alerts_generated,
                    errors_json, summary_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    cycle_result.get("started_at") or cycle_result.get("timestamp") or datetime.now().isoformat(),
                    cycle_result.get("finished_at") or datetime.now().isoformat(),
                    int(cycle_result.get("documents_collected", 0)),
                    int(cycle_result.get("documents_analyzed", 0)),
                    int(cycle_result.get("alerts_generated", 0)),
                    json.dumps(cycle_result.get("errors", []), ensure_ascii=False, default=str),
                    json.dumps(cycle_result.get("summary", {}), ensure_ascii=False, default=str),
                ),
            )
        return True

    def get_monitoring_cycles(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retorna histórico de ciclos mais recentes."""
        safe_limit = max(1, int(limit or 20))
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT cycle_id, started_at, finished_at, documents_collected, documents_analyzed, alerts_generated, errors_json, summary_json
                FROM monitoring_cycles
                ORDER BY datetime(finished_at) DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        output: List[Dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "cycle_id": row["cycle_id"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "documents_collected": row["documents_collected"],
                    "documents_analyzed": row["documents_analyzed"],
                    "alerts_generated": row["alerts_generated"],
                    "errors": json.loads(row["errors_json"] or "[]"),
                    "summary": json.loads(row["summary_json"] or "{}"),
                }
            )
        return output

    def get_processed_documents(self) -> List[Dict[str, Any]]:
        """Retorna documentos já processados"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, source, document_type, url, published_date, processed_at
                FROM documents
                WHERE processed = 1
                ORDER BY datetime(processed_at) DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def update_processing_status(self, doc_id: str, status: str) -> bool:
        """Atualiza status de processamento"""
        normalized = (status or "").strip().lower()
        processed = normalized in {"processed", "done", "ok", "true", "1"}
        processed_at = datetime.now().isoformat() if processed else None
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE documents
                SET processed = ?, processed_at = ?
                WHERE id = ?
                """,
                (1 if processed else 0, processed_at, doc_id),
            )
            return cursor.rowcount > 0

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas de processamento"""
        with self._get_connection() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_documents,
                    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) AS processed
                FROM documents
                """
            ).fetchone()
            by_source_rows = conn.execute(
                """
                SELECT source, COUNT(*) AS c
                FROM documents
                GROUP BY source
                """
            ).fetchall()
            last_update_row = conn.execute(
                """
                SELECT MAX(COALESCE(processed_at, collected_at)) AS last_update
                FROM documents
                """
            ).fetchone()

        total_documents = totals["total_documents"] or 0
        processed = totals["processed"] or 0
        return {
            "total_documents": total_documents,
            "processed": processed,
            "pending": total_documents - processed,
            "by_source": {row["source"]: row["c"] for row in by_source_rows},
            "last_update": last_update_row["last_update"],
        }
