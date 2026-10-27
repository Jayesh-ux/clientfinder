"""Database connectivity helpers for the CLIENTFINDER catalog.

DB path resolution precedence:
    1. CLIENTFINDER_DB_PATH environment variable
    2. default: <repo>/pipeline/crm.db (shared with the v2 pipeline)

Kept stdlib-only (sqlite3), consistent with the existing pipeline module.
"""

from service_catalog import config

get_db_path = config.get_db_path

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


def connect():
    """Resolve via the module-level get_db_path so tests can override it."""
    return config.connect(get_db_path())