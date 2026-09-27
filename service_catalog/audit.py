"""Audit logging for CLIENTFINDER v3 (Phase 5).

Purely additive: records WHO did WHAT to WHICH entity, plus a human-readable
reason when supplied. Writes to pipeline/crm.db (audit_log table) if the
migration V5 has been applied, otherwise degrades to a stderr log line so older
databases are never broken by the audit layer.
"""

import json
import logging
import os
from datetime import datetime, timezone

from service_catalog import db as db_module

logger = logging.getLogger(__name__)

AUDIT_ENABLED = os.environ.get("CLIENTFINDER_AUDIT", "1") != "0"


def _db_path():
    return db_module.get_db_path()


def _table_exists(conn, table):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return row is not None


def log(actor, action, entity, entity_id, before=None, after=None, reason=None, tags=None):
    """Append an audit entry. before/after and tags are JSON-encoded."""
    if not AUDIT_ENABLED:
        return
    import sqlite3
    try:
        db_path = _db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            if not _table_exists(conn, "audit_log"):
                logger.debug("audit_log table missing; skipping audit write")
                return
            conn.execute(
                "INSERT INTO audit_log (ts, actor, action, entity, entity_id,"
                " before, after, reason, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), actor, action, entity,
                 str(entity_id) if entity_id is not None else None,
                 json.dumps(before) if before is not None else None,
                 json.dumps(after) if after is not None else None,
                 reason,
                 json.dumps(tags) if tags else None),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:  # pragma: no cover - audit must never break the caller
        logger.warning(f"Audit log write failed: {e}")