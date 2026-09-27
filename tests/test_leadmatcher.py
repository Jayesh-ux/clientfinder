import sqlite3


def test_build_context_uses_fields(leads_populated):
    from service_catalog.leadmatcher import _lookup_lead, build_context
    conn = sqlite3.connect(str(leads_populated))
    lead = _lookup_lead(conn, "lead-1")
    conn.close()
    assert lead is not None
    context = build_context(lead)
    assert "Pine Valley Cafe" in context
    assert "customers" in context


def test_match_single_lead_persists(leads_populated):
    from service_catalog.leadmatcher import for_lead, get_stored_matches
    results = for_lead("lead-1", top_k=3, min_score=1)
    assert results, "expected at least one match for lead-1"
    assert any(r["solution"]["slug"] == "lead-gen-automation" for r in results)
    for r in results:
        assert "score" in r
        assert "total" in r["score"]

    stored = get_stored_matches("lead-1")
    conn = sqlite3.connect(str(leads_populated))
    match_rows = conn.execute(
        "SELECT COUNT(*) FROM lead_matches WHERE lead_id = 'lead-1'").fetchone()[0]
    score_row = conn.execute(
        "SELECT total, tier FROM lead_scores WHERE lead_id = 'lead-1'").fetchone()
    conn.close()
    assert match_rows >= 1
    assert score_row is not None
    assert stored["best"] is not None


def test_match_construction_lead(leads_populated):
    from service_catalog.leadmatcher import for_lead
    results = for_lead("lead-2", top_k=3, min_score=1)
    assert results, "expected at least one match for lead-2"
    assert any(r["solution"]["slug"] == "realtime-tracking-dashboard" for r in results)


def test_match_all_dry_run(leads_populated):
    from service_catalog.leadmatcher import match_all
    conn = sqlite3.connect(str(leads_populated))
    before = conn.execute("SELECT COUNT(*) FROM lead_matches").fetchone()[0]
    conn.close()
    summary = match_all(top_k=3, min_score=1, persist=False)
    conn = sqlite3.connect(str(leads_populated))
    after = conn.execute("SELECT COUNT(*) FROM lead_matches").fetchone()[0]
    conn.close()
    assert summary["leads_seen"] >= 2
    assert summary["matched"] >= 1
    assert after == before, "dry-run must not persist"


def test_digital_presence_pattern_matches_and_explains(leads_populated):
    from service_catalog.leadmatcher import for_lead
    results = for_lead("lead-3", top_k=3, min_score=1)
    assert results, "expected at least one match for lead-3"
    assert any(r["solution"]["slug"] == "digital-presence-booking" for r in results)
    for r in results:
        assert r.get("explanation"), "matches must carry a human-readable explanation"
        assert "Suggested solution" in r["explanation"]