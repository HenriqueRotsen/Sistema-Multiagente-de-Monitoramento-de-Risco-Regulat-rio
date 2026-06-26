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
