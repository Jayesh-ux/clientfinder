import sqlite3


def _tables(db_path):
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return {r[0] for r in rows}


def test_migrations_create_catalog_tables(init_db_connected, db_path):
    tables = _tables(db_path)
    expected = {
        "schema_migrations",
        "capabilities",
        "portfolio_evidence",
        "solution_templates",
        "solution_capabilities",
        "solution_evidence",
        "problem_patterns",
    }
    assert expected.issubset(tables)


def test_migrations_idempotent(init_db_connected, db_path):
    from pipeline import migrate as mig
    before = _tables(db_path)
    applied = mig.migrate(db_path, verbose=False)
    assert applied == []
    assert _tables(db_path) == before


def test_seed_idempotent(init_db_connected, db_path):
    from service_catalog.seed import seed
    conn = sqlite3.connect(str(db_path))
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("capabilities", "portfolio_evidence", "solution_templates",
                        "problem_patterns")}
    conn.close()
    seed()
    conn = sqlite3.connect(str(db_path))
    counts_after = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    for t in ("capabilities", "portfolio_evidence", "solution_templates",
                              "problem_patterns")}
    conn.close()
    assert counts == counts_after


def test_seed_populates_catalog(init_db_connected, db_path):
    conn = sqlite3.connect(str(db_path))
    caps = conn.execute("SELECT COUNT(*) FROM capabilities").fetchone()[0]
    sols = conn.execute("SELECT COUNT(*) FROM solution_templates").fetchone()[0]
    pats = conn.execute("SELECT COUNT(*) FROM problem_patterns").fetchone()[0]
    conn.close()
    assert caps >= 13
    assert sols >= 5
    assert pats >= 5