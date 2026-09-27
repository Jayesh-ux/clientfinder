import sqlite3


def test_audit_writes_via_env(init_db_connected, db_path):
    from service_catalog import audit
    audit.log(
        actor="tester", action="create", entity="capability",
        entity_id=1, before=None, after={"slug": "x"}, reason="test", tags=["suite"])
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT actor, action, entity, reason FROM audit_log").fetchall()
    conn.close()
    assert any(r == ("tester", "create", "capability", "test") for r in rows)


def test_audit_never_raises(init_db_connected):
    from service_catalog import audit
    try:
        audit.log(actor="tester", action="boom", entity="missing",
                  entity_id=-1, after=None, before=None)
    except Exception as e:  # pragma: no cover
        raise AssertionError(f"audit.log raised: {e}")


def test_score_tables_created(init_db_connected, db_path):
    conn = sqlite3.connect(str(db_path))
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert {"audit_log", "lead_matches", "lead_scores", "schema_migrations"}.issubset(tables)