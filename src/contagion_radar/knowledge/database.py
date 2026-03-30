"""SQLite database schema management for 3 separate databases.

- metrics.db:   time-series numerical data (TVL, price, gas, flows)
- corpus.db:    unstructured text (tweets, articles) with FTS5
- knowledge.db: hypotheses, anomalies, precedents, relationships, calibrations
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

_DEFAULT_DATA_DIR = Path("./data")


def _get_data_dir() -> Path:
    d = _DEFAULT_DATA_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── metrics.db ──────────────────────────────────────────────────

METRICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    entity TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_lookup
    ON metrics (entity, metric, timestamp);

CREATE INDEX IF NOT EXISTS idx_metrics_time
    ON metrics (timestamp);
"""


# ── corpus.db ───────────────────────────────────────────────────

CORPUS_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,
    entity_mentions TEXT NOT NULL DEFAULT '[]',
    text TEXT NOT NULL,
    category TEXT,
    sentiment_score REAL,
    language TEXT DEFAULT 'en'
);

CREATE INDEX IF NOT EXISTS idx_corpus_time
    ON documents (timestamp);

CREATE INDEX IF NOT EXISTS idx_corpus_source
    ON documents (source, timestamp);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
    text,
    content='documents',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO documents_fts(rowid, text) VALUES (new.id, new.text);
END;
"""


# ── knowledge.db ────────────────────────────────────────────────

KNOWLEDGE_SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    first_tracked TEXT,
    last_updated TEXT,
    total_hypotheses_generated INTEGER DEFAULT 0,
    total_anomalies_detected INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    failure_mode TEXT NOT NULL,
    cause_chain TEXT NOT NULL DEFAULT '[]',
    probability REAL NOT NULL,
    data_signals TEXT NOT NULL DEFAULT '[]',
    generated_at TEXT NOT NULL,
    generated_from_score REAL,
    status TEXT NOT NULL DEFAULT 'active',
    current_confidence REAL DEFAULT 0.5,
    confidence_trajectory TEXT DEFAULT '[]',
    outcome_description TEXT,
    resolved_at TEXT,
    model_used TEXT,
    FOREIGN KEY (entity_id) REFERENCES entities(id)
);

CREATE INDEX IF NOT EXISTS idx_hyp_entity
    ON hypotheses (entity_id, status);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hypothesis_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metric TEXT NOT NULL,
    observed_value REAL,
    expected_direction TEXT,
    actual_direction TEXT,
    supports INTEGER NOT NULL,
    weight REAL DEFAULT 1.0,
    context TEXT,
    FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    engine TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    severity REAL NOT NULL,
    context TEXT,
    composite_score_at_detection REAL,
    cadence_at_detection REAL,
    related_hypothesis_ids TEXT DEFAULT '[]',
    resolved INTEGER DEFAULT 0,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_anomaly_entity
    ON anomalies (entity_id, detected_at);

CREATE TABLE IF NOT EXISTS precedents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    feature_vector TEXT NOT NULL DEFAULT '{}',
    lead_time_hours REAL,
    timeline TEXT DEFAULT '[]',
    lessons TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_a TEXT NOT NULL,
    entity_b TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength REAL NOT NULL,
    discovered_at TEXT NOT NULL,
    last_observed TEXT,
    source TEXT,
    evidence TEXT,
    UNIQUE(entity_a, entity_b, relationship_type)
);

CREATE TABLE IF NOT EXISTS calibrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    engine TEXT NOT NULL,
    metric TEXT NOT NULL,
    old_value REAL,
    new_value REAL,
    reason TEXT NOT NULL,
    triggered_by TEXT,
    performance_before TEXT,
    performance_after TEXT
);

CREATE TABLE IF NOT EXISTS operator_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_entity TEXT,
    target_alert_id TEXT,
    reason TEXT NOT NULL,
    parameters TEXT DEFAULT '{}',
    expires_at TEXT,
    operator_id TEXT
);

CREATE TABLE IF NOT EXISTS ai_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    call_type TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    composite_score_at_call REAL,
    trigger_reason TEXT,
    model TEXT,
    latency_ms INTEGER
);
"""


def init_metrics_db(data_dir: Path | None = None) -> Path:
    d = data_dir or _get_data_dir()
    db_path = d / "metrics.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(METRICS_SCHEMA)
    conn.close()
    return db_path


def init_corpus_db(data_dir: Path | None = None) -> Path:
    d = data_dir or _get_data_dir()
    db_path = d / "corpus.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(CORPUS_SCHEMA)
    conn.close()
    return db_path


def init_knowledge_db(data_dir: Path | None = None) -> Path:
    d = data_dir or _get_data_dir()
    db_path = d / "knowledge.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(KNOWLEDGE_SCHEMA)
    conn.close()
    return db_path


def init_all_databases(data_dir: Path | None = None) -> dict[str, Path]:
    """Initialize all 3 databases, return their paths."""
    d = data_dir or _get_data_dir()
    return {
        "metrics": init_metrics_db(d),
        "corpus": init_corpus_db(d),
        "knowledge": init_knowledge_db(d),
    }
