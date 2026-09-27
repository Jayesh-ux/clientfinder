"""CLIENTFINDER v3 migration runner.

Applies ordered .sql files under pipeline/migrations to the sqlite database.
- Creates the schema_migrations bookkeeping table.
- Runs each pending migration inside its own transaction.
- Backs up the database file before the first migration run.
- Optional catalog seeding via --seed.

Usage:
    python pipeline/migrate.py [db_path] [--seed] [--no-seed]

DB resolution precedence:
    1. positional db_path argument
    2. CLIENTFINDER_DB_PATH environment variable
    3. default: <repo>/pipeline/crm.db
"""

import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "pipeline" / "crm.db"


def resolve_db_path(argv_db_path=None):
    if argv_db_path:
        return Path(argv_db_path)
    env_path = os.environ.get("CLIENTFINDER_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def connect(db_path):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def collect_sql_files():
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def backup_if_present(db_path):
    if db_path.is_file():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = db_path.with_name(f"{db_path.name}.bak-{stamp}")
        shutil.copy2(str(db_path), str(backup))
        print(f"Backed up existing DB to {backup}")


def migrate(db_path, verbose=True):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY,"
        " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    applied_rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    applied = {row["version"] for row in applied_rows}
    conn.close()

    files = [p for p in collect_sql_files() if p.stem not in applied]

    if db_path.is_file() and files:
        backup_if_present(db_path)

    migrated = []
    for path in files:
        version = path.stem
        if version in applied:
            continue
        if verbose:
            print(f"Applying {path.name}")
        conn = connect(db_path)
        try:
            conn.executescript(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
            conn.commit()
        except Exception:
            conn.rollback()
            conn.close()
            raise
        conn.close()
        migrated.append(version)

    if verbose:
        if migrated:
            print(f"Applied migrations: {migrated}")
        else:
            print("No pending migrations.")
    return migrated


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    seed_flag = "--seed" in argv
    no_seed = "--no-seed" in argv
    positional = [a for a in argv if not a.startswith("--")]

    db_path = resolve_db_path(positional[0] if positional else None)
    migrate(db_path)

    if seed_flag and not no_seed:
        from service_catalog.seed import seed
        seed(override_db_path=db_path)
        print("Catalog seed complete.")
    else:
        print("Tip: run with --seed to populate the catalog from seed data.")


if __name__ == "__main__":
    main()