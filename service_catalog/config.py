"""Central path + environment resolution for CLIENTFINDER.

Every pipeline script, catalog module and test resolves files through here so
the repo works from any CWD, on any OS, with or without a .env file.

Layout (all repo-root anchored):
    pipeline/crm.db        SQLite CRM (override: CLIENTFINDER_DB_PATH)
    data/raw/              raw scrape / import payloads (git-ignored)
    data/outreach/         generated dossiers, call lists, exports (git-ignored)
    .env                   local secrets (git-ignored, never committed)

Env precedence:
    1. real environment (os.environ)
    2. .env at repo root
"""

import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PIPELINE_DIR = REPO_ROOT / "pipeline"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
OUTREACH_DIR = DATA_DIR / "outreach"
DEFAULT_DB_PATH = PIPELINE_DIR / "crm.db"
ENV_PATH = REPO_ROOT / ".env"

_TRUTHY = {"1", "true", "yes", "on"}


def load_env(path=None):
    """Load KEY=VALUE pairs from .env into os.environ without clobbering real env.

    Returns the dict of keys that were set. Safe to call repeatedly.
    """
    env_file = Path(path) if path else ENV_PATH
    loaded = {}
    if not env_file.is_file():
        return loaded
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        os.environ.setdefault(key, value)
        loaded[key] = value
    return loaded


def get_db_path():
    """CLIENTFINDER_DB_PATH if set, else <repo>/pipeline/crm.db."""
    env_path = os.environ.get("CLIENTFINDER_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_test_db_path():
    """Path used by integration-style tests that need real CRM rows."""
    return Path(os.environ.get("TEST_CRM_DB") or get_db_path())


def connect(db_path=None):
    """Open the CRM with foreign keys on and Row access."""
    target = Path(db_path) if db_path else get_db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_data_dirs():
    """Create the git-ignored working dirs. Returns {name: Path}."""
    dirs = {"raw": RAW_DIR, "outreach": OUTREACH_DIR}
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUTHY


load_env()