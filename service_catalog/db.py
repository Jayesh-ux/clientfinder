"""Database connectivity helpers for the CLIENTFINDER catalog.

DB path resolution precedence:
    1. CLIENTFINDER_DB_PATH environment variable
    2. default: <repo>/pipeline/crm.db (shared with the v2 pipeline)

Kept stdlib-only (sqlite3), consistent with the existing pipeline module.
"""

import os
import sqlite3
from pathlib import Path


BOOLEAN_COLUMNS = {"verified", "is_active", "send_enabled"}


def row_to_dict(row):
    """Convert a sqlite3.Row to a dict, coercing 0/1 boolean columns to Python bool."""
    if row is None:
        return None
    d = dict(row)
    for name in BOOLEAN_COLUMNS:
        if name in d and d[name] is not None:
            d[name] = bool(d[name])
    return d


def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]


def get_db_path():
    env_path = os.environ.get("CLIENTFINDER_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent.parent / "pipeline" / "crm.db"


def connect():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn