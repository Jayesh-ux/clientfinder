-- CLIENTFINDER v3
-- Migration 0001: Flexible dynamic capability catalog
-- Additive only. Preserves existing v2 tables (leads, interactions, fields).
-- Schema bookkeeping (schema_migrations) is created by the runner.

CREATE TABLE IF NOT EXISTS portfolio_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    role TEXT,
    description TEXT,
    skills_used TEXT,              -- JSON array of capability slugs
    url TEXT,
    date_label TEXT,
    outcome TEXT,
    provenance TEXT NOT NULL DEFAULT 'reported',
    verified BOOLEAN NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    proficiency TEXT NOT NULL DEFAULT 'intermediate',   -- beginner|limited|intermediate|advanced|expert
    verification_level TEXT NOT NULL DEFAULT 'unvalidated', -- verified_industry|verified_project|familiarity|unvalidated
    evidence_id INTEGER REFERENCES portfolio_evidence(id) ON DELETE SET NULL,
    proven_note TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS solution_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    summary TEXT,
    problem_text TEXT,
    deliverables TEXT,             -- JSON array of strings
    typical_effort_label TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS solution_capabilities (
    solution_id INTEGER NOT NULL REFERENCES solution_templates(id) ON DELETE CASCADE,
    capability_id INTEGER NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
    PRIMARY KEY (solution_id, capability_id)
);

CREATE TABLE IF NOT EXISTS solution_evidence (
    solution_id INTEGER NOT NULL REFERENCES solution_templates(id) ON DELETE CASCADE,
    evidence_id INTEGER NOT NULL REFERENCES portfolio_evidence(id) ON DELETE CASCADE,
    PRIMARY KEY (solution_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS problem_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    keywords TEXT NOT NULL,        -- JSON array of search/matching terms
    description TEXT,
    solution_id INTEGER NOT NULL REFERENCES solution_templates(id) ON DELETE CASCADE,
    urgency_hint TEXT,
    size_hint TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);