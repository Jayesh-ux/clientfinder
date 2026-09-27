"""Fit scoring for CLIENTFINDER v3 (Phase 4).

Given a business-problem description, a matched solution, and optional context
(company size, urgency signals), produce a structured fit score with an
explanation per component. This is a heuristic baseline; LLM refinement can be
layered on later without changing the output contract.

Output shape (stable contract for downstream dashboards/reports):
    {
        "total": 0..100,
        "components": {"need_fit", "scale_fit", "urgency", "evidence_confidence"},
        "reasons": [...],
        "scorecard": [...]
    }
"""

import re


def _signal_hits(text, signals):
    text = (text or "").lower()
    return [s for s in signals if s in text]


URGENCY_SIGNALS = [
    "asap", "urgent", "immediately", "now", "losing", "problem", "frustrated",
    "stop", "cannot", "can't", "too slow", "waste", "manual", "errors",
]
GROWTH_SIGNALS = [
    "grow", "more customers", "scaling", "expansion", "revenue", "sales",
    "acquisition", "leads", "outreach",
]
SCALE_SIGNALS = [
    "many locations", "branches", "hundreds", "thousands", "team of",
    "large", "chain", "franchise", "13000", "enterprise",
]
STRUCTURE_SIGNALS = {
    "small": ["small", "mom and pop", "friendly", "local", "startup",
              "just me", "owner-run"],
    "medium": ["growing", "several", "multiple", "franchise", "team"],
    "large": ["large", "chain", "enterprise", "corporate", "many branches",
              "hundreds", "thousands"],
}


def score_need_fit(match_score, description):
    """How well the matched solution addresses the described problem."""
    base = min(match_score * 20, 80)
    description = description or ""
    if any(kw in description.lower() for kw in GROWTH_SIGNALS):
        base = min(base + 10, 90)
    return base


def score_scale_fit(size_text, default=60):
    """Match of organization size to solution scope."""
    size_text = (size_text or "").lower()
    for scale, signals in STRUCTURE_SIGNALS.items():
        if any(s in size_text for s in signals):
            return {"small": 65, "medium": 80, "large": 90}[scale]
    return default


def score_urgency(text):
    hits = _signal_hits(text, URGENCY_SIGNALS)
    if len(hits) >= 3:
        return 90
    if hits:
        return 60 + 10 * len(hits)
    return 35


def score_evidence_confidence(solution):
    evidence = solution.get("evidence") or []
    verified = [e for e in evidence if e.get("verified")]
    if verified:
        return 95
    if evidence:
        return 70
    return 35


def score_lead(description, match_score, solution, size_text=None, urgency_text=None):
    """Compute the fit scorecard for one lead against one matched solution."""
    need = score_need_fit(match_score, description)
    scale = score_scale_fit(size_text or description)
    urgency = score_urgency(urgency_text or description)
    confidence = score_evidence_confidence(solution)

    total = round(
        0.40 * need + 0.20 * scale + 0.20 * urgency + 0.20 * confidence
    )
    total = max(0, min(100, total))

    reasons = [
        f"Match score {match_score} indicates strong problem overlap"
        if match_score >= 3 else
        f"Match score {match_score} indicates partial problem overlap",
        f"Need fit: {need}/100",
        f"Scale fit: {scale}/100",
        f"Urgency: {urgency}/100",
        f"Evidence confidence: {confidence}/100",
    ]

    return {
        "total": total,
        "components": {
            "need_fit": need,
            "scale_fit": scale,
            "urgency": urgency,
            "evidence_confidence": confidence,
        },
        "reasons": reasons,
        "scorecard": [
            {"component": "need_fit", "score": need, "weight": 0.40},
            {"component": "scale_fit", "score": scale, "weight": 0.20},
            {"component": "urgency", "score": urgency, "weight": 0.20},
            {"component": "evidence_confidence", "score": confidence, "weight": 0.20},
        ],
        "tier": "hot" if total >= 75 else "warm" if total >= 50 else "cold",
    }


def explain(score_result):
    """Human-readable one-liners for the score."""
    return " | ".join(
        f"{c['component']}={c['score']}" for c in score_result["scorecard"])