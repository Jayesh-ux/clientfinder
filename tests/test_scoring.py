from service_catalog.scoring import score_lead, score_need_fit, score_urgency


def _fake_solution(verified=False, has_evidence=False):
    return {"evidence": [{"verified": verified}] if has_evidence or verified else []}


def test_urgency_scoring():
    assert score_urgency("") == 35
    assert score_urgency("urgent manual errors happening now") == 90
    assert score_urgency("nothing") == 35


def test_need_fit_caps():
    assert score_need_fit(10, "we need to grow and get more customers") == 90
    assert score_need_fit(1, "generic") <= 45


def test_score_lead_tiers():
    sol_verified = _fake_solution(verified=True)
    hot = score_lead(
        "urgent need for more customers and sales leads now",
        5, sol_verified, size_text="large chain")
    assert hot["total"] >= 75
    assert hot["tier"] == "hot"

    sol_none = _fake_solution()
    cold = score_lead("vague text with no signals", 1, sol_none)
    assert cold["total"] <= 60
    assert cold["tier"] in ("warm", "cold")


def test_score_contract():
    result = score_lead("some manual spreadsheet work", 2, _fake_solution())
    assert set(result["components"]) == {
        "need_fit", "scale_fit", "urgency", "evidence_confidence"}
    assert 0 <= result["total"] <= 100
    assert len(result["reasons"]) >= 3
    assert len(result["scorecard"]) == 4