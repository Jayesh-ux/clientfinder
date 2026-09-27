-- CLIENTFINDER v3
-- Migration 0002: audit log, lead match, and lead score persistence.
-- Additive only. Never alters existing v2 tables.

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    before TEXT,
    after TEXT,
    reason TEXT,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log (ts);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log (entity, entity_id);

CREATE TABLE IF NOT EXISTS lead_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT NOT NULL,
    solution_slug TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    matched_keywords TEXT,
    pattern_ids TEXT,
    evidence_note TEXT,
    explanation TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lead_matches_lead ON lead_matches (lead_id);

CREATE TABLE IF NOT EXISTS lead_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT NOT NULL UNIQUE,
    total INTEGER NOT NULL DEFAULT 0,
    tier TEXT NOT NULL DEFAULT 'cold',
    components TEXT,
    reasons TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_lead_scores_total ON lead_scores (total desc);