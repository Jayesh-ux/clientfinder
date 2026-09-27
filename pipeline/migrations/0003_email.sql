-- CLIENTFINDER v3
-- Migration 0003: email subsystem tables.
-- Additive only. Drafts default; nothing auto-sends unless explicitly enabled.

CREATE TABLE IF NOT EXISTS email_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    smtp_host TEXT,
    smtp_port INTEGER,
    smtp_user TEXT,
    imap_host TEXT,
    imap_port INTEGER,
    imap_user TEXT,
    send_enabled BOOLEAN NOT NULL DEFAULT 0,
    from_name TEXT,
    from_email TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS email_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT,
    solution_slug TEXT,
    account_id INTEGER REFERENCES email_accounts(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',   -- draft|approved|sent|cancelled
    send_after TEXT,
    tags TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_email_drafts_lead ON email_drafts (lead_id);
CREATE INDEX IF NOT EXISTS idx_email_drafts_status ON email_drafts (status);

CREATE TABLE IF NOT EXISTS email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER REFERENCES email_accounts(id) ON DELETE SET NULL,
    mailbox TEXT,
    uid TEXT,
    message_id TEXT,
    subject TEXT,
    body TEXT,
    from_addr TEXT,
    to_addr TEXT,
    date TEXT,
    replied BOOLEAN NOT NULL DEFAULT 0,
    raw TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_email_messages_acc_uid ON email_messages (account_id, uid);
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_messages_msgid ON email_messages (message_id);