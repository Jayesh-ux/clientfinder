def test_capabilities_crud(client):
    r = client.get("/catalog/capabilities")
    assert r.status_code == 200
    assert len(r.json()) >= 13

    r = client.post("/catalog/capabilities", json={
        "slug": "rust", "name": "Rust", "category": "Backend",
        "description": "test capability", "proficiency": "beginner"})
    assert r.status_code == 201
    created = r.json()
    assert created["slug"] == "rust"

    r = client.post("/catalog/capabilities", json={
        "slug": "rust", "name": "Rust", "category": "Backend"})
    assert r.status_code == 409

    r = client.patch(f"/catalog/capabilities/{created['id']}", json={
        "verification_level": "familiarity"})
    assert r.status_code == 200
    assert r.json()["verification_level"] == "familiarity"

    r = client.delete(f"/catalog/capabilities/{created['id']}")
    assert r.status_code == 204


def test_evidence_crud(client):
    r = client.post("/catalog/evidence", json={
        "project_name": "FixtureCo", "role": "Builder",
        "description": "fixture project", "skills_used": ["python"]})
    assert r.status_code == 201
    ev = r.json()
    assert ev["provenance"] == "reported"

    r = client.patch(f"/catalog/evidence/{ev['id']}", json={"verified": True})
    assert r.status_code == 200
    assert r.json()["verified"] is True

    r = client.get("/catalog/evidence?verified_only=true")
    ids = [e["id"] for e in r.json()]
    assert ev["id"] in ids

    r = client.delete(f"/catalog/evidence/{ev['id']}")
    assert r.status_code == 204


def test_solution_crud_and_links(client):
    r = client.post("/catalog/solutions", json={
        "slug": "fixture-solution", "name": "Fixture Solution",
        "summary": "fixture", "capability_slugs": ["python", "fastapi"],
        "evidence_ids": []})
    assert r.status_code == 201
    sol = r.json()
    assert sol["capabilities"][0]["slug"] == "python" or sol["capabilities"][0]["slug"] == "fastapi"

    r = client.get(f"/catalog/solutions/{sol['id']}")
    assert r.status_code == 200

    r = client.delete(f"/catalog/solutions/{sol['id']}")
    assert r.status_code == 204


def test_pattern_crud(client):
    r = client.post("/catalog/patterns", json={
        "slug": "fixture-pattern", "label": "Fixture pattern",
        "keywords": ["fixture"], "solution_slug": "lead-gen-automation"})
    assert r.status_code == 201
    pat = r.json()

    r = client.post("/catalog/patterns", json={
        "slug": "bad-pattern", "label": "bad",
        "keywords": ["x"], "solution_slug": "does-not-exist"})
    assert r.status_code == 409

    r = client.delete(f"/catalog/patterns/{pat['id']}")
    assert r.status_code == 204


def test_match_returns_solution(client):
    r = client.get("/catalog/match",
                   params={"text": "We rely on referrals and have no systematic way "
                                   "to find new customers; we need more leads and "
                                   "grow sales without inbound enquiry"})
    assert r.status_code == 200
    results = r.json()
    assert results, "expected at least one matched solution"
    assert any(s["solution"]["slug"] == "lead-gen-automation" for s in results)

    r = client.get("/catalog/match", params={"text": ""})
    assert r.status_code == 400


def test_lead_match_api(leads_populated, client):
    r = client.get("/catalog/leads/lead-1/match")
    assert r.status_code == 200
    results = r.json()
    assert results
    assert any(s["solution"]["slug"] == "lead-gen-automation" for s in results)

    r = client.get("/catalog/leads/lead-1/matches")
    assert r.status_code == 200
    assert r.json()["best"] is not None

    r = client.get("/catalog/leads/nope/match")
    assert r.status_code == 404


def test_email_api_draft_lifecycle(client):
    r = client.post("/email/accounts",
                    json={"name": "API Sender", "from_email": "a@b.com",
                          "smtp_host": "smtp.example.com", "smtp_port": 587})
    assert r.status_code == 201
    acct = r.json()
    assert acct["send_enabled"] is False

    r = client.post("/email/drafts",
                    json={"subject": "S1", "body": "B1", "account_id": acct["id"]})
    assert r.status_code == 201
    draft = r.json()
    assert draft["status"] == "draft"

    r = client.get("/email/drafts?status=draft")
    assert any(d["id"] == draft["id"] for d in r.json())

    # send without approval -> 400 (guard)
    r = client.post(f"/email/drafts/{draft['id']}/send")
    assert r.status_code == 400

    r = client.post(f"/email/drafts/{draft['id']}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    r = client.post("/email/accounts/{}/enable".format(acct["id"]),
                    params={"enabled": "true"})
    assert r.status_code == 200

    # no lead email -> structured 400 before any network
    r = client.post(f"/email/drafts/{draft['id']}/send")
    assert r.status_code == 400

    r = client.get("/email/inbox")
    assert r.status_code == 200
    assert r.json() == []


def test_match_with_scoring(client):
    r = client.get("/catalog/match",
                   params={"text": "urgent reliance on referrals and no way to find "
                                   "new customers; can't bring in more leads",
                           "include_score": "true",
                           "size_text": "large chain"})
    assert r.status_code == 200
    results = r.json()
    assert results
    top = results[0]
    assert "score" in top
    components = top["score"]["components"]
    assert set(components) == {
        "need_fit", "scale_fit", "urgency", "evidence_confidence"}
    assert 0 <= top["score"]["total"] <= 100


def test_offerings_api_lists_and_drafts(client):
    r = client.get("/offerings")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 15
    slugs = {o["solution_slug"] for o in body["offerings"]}
    assert "inventory-stock-automation" in slugs
    assert "digital-presence-booking" in slugs

    r = client.get("/offerings/inventory-stock-automation/draft",
                   params={"business": "Acme Store", "area": "Delhi"})
    assert r.status_code == 200
    draft = r.json()
    assert "Acme Store" in draft["body"]
    assert draft["deliverables"]

    r = client.get("/offerings/does-not-exist")
    assert r.status_code == 404