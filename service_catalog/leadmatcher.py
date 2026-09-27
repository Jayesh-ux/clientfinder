"""Match existing CRM leads against the flexible capability catalog.

Phase 6-lite: builds a business-context description for each lead from the v2
`leads` table, runs the catalog matcher + scorer, and persists the results into
`lead_matches` and `lead_scores` (migration 0002 tables). Purely additive to
the v2 pipeline; it never mutates the leads table itself.

Matching is NEED-driven, never niche-driven: only observed symptom fields are
used to match (website status, observations, notes, etc.). The business name,
category, niche, and location are excluded from the matcher so the same symptom
in any industry resolves to the same solution.
"""

import json
import sqlite3

from service_catalog.db import connect
from service_catalog.matching import match_business_problem
from service_catalog.scoring import score_lead

SYMPTOM_FIELDS = [
    "website_status", "seo_observation", "conversion_observation",
    "booking_observation", "social_activity_observation", "personalisation_note",
    "recommended_offer", "offer_angle", "notes",
]

CONTEXT_FIELDS = [
    "business_name", "business_category", "sub_category", "niche", "city", "area",
    "website_status", "seo_observation", "conversion_observation",
    "booking_observation", "social_activity_observation", "personalisation_note",
    "recommended_offer", "offer_angle", "notes",
]


def build_match_text(lead):
    """Compose ONLY the observed symptoms; no name/category/niche/location."""
    return " ".join(
        str(lead.get(f)) for f in SYMPTOM_FIELDS if lead.get(f))


def build_context(lead):
    """Compose a full text blob (symptoms + identity) for scale/urgency signals."""
    parts = []
    for field in CONTEXT_FIELDS:
        value = lead.get(field)
        if value:
            parts.append(str(value))
    return " ".join(parts)


def _lookup_lead(conn, lead_id):
    cur = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,))
    row = cur.fetchone()
    if row is None:
        return None
    if isinstance(row, sqlite3.Row):
        return dict(row)
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def _clear_previous(conn, lead_id):
    conn.execute("DELETE FROM lead_matches WHERE lead_id = ?", (lead_id,))
    conn.execute("DELETE FROM lead_scores WHERE lead_id = ?", (lead_id,))


def _persist_matches(conn, lead_id, results):
    for item in results:
        conn.execute(
            "INSERT INTO lead_matches (lead_id, solution_slug, score, matched_keywords,"
            " pattern_ids, evidence_note, explanation)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (lead_id, item["solution"]["slug"], item["match_score"],
             json.dumps(item["matched_keywords"]),
             json.dumps(item["pattern_ids"]),
             item["evidence_note"],
             item.get("explanation")),
        )


def _persist_best_score(conn, lead_id, results):
    if not results:
        return
    best = max(results, key=lambda r: r.get("score", {}).get("total", 0))
    score = best.get("score", {})
    conn.execute(
        "INSERT OR REPLACE INTO lead_scores (lead_id, total, tier, components, reasons,"
        " updated_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (lead_id, score.get("total", 0), score.get("tier", "cold"),
         json.dumps(score.get("components", {})),
         json.dumps(score.get("reasons", []))),
    )


def for_lead(lead_id, top_k=5, min_score=1, persist=True):
    """Match a single lead by lead_id. Returns the raw results (unscored).

    With persist=True, writes lead_matches + best lead_scores rows.
    """
    conn = connect()
    try:
        lead = _lookup_lead(conn, lead_id)
        if lead is None:
            return None
        context = build_context(lead)
        results = match_business_problem(context, top_k=top_k, min_score=min_score)
        for item in results:
            item["score"] = score_lead(
                description=context,
                match_score=item["match_score"],
                solution=item["solution"],
                size_text="",
                urgency_text=context,
            )
        if persist:
            _clear_previous(conn, lead_id)
            _persist_matches(conn, lead_id, results)
            _persist_best_score(conn, lead_id, results)
            conn.commit()
        return results
    finally:
        conn.close()


def match_all(top_k=5, min_score=1, limit=None, persist=True):
    """Match every lead in the table. Returns a per-lead summary.

    Safe to run repeatedly: prior matches for a lead are replaced.
    """
    conn = connect()
    try:
        q = "SELECT lead_id FROM leads"
        if limit:
            q += f" LIMIT {int(limit)}"
        rows = conn.execute(q).fetchall()
    finally:
        conn.close()

    matched = 0
    skipped = 0
    for row in rows:
        lead_id = row["lead_id"]
        results = for_lead(lead_id, top_k=top_k, min_score=min_score, persist=persist)
        if results:
            matched += 1
        else:
            skipped += 1
    return {"leads_seen": len(rows), "matched": matched, "no_match": skipped}


def get_stored_matches(lead_id):
    """Fetch persisted matches + best score for a lead."""
    conn = connect()
    try:
        matches = [dict(r) for r in conn.execute(
            "SELECT * FROM lead_matches WHERE lead_id = ? ORDER BY score DESC",
            (lead_id,)).fetchall()]
        for m in matches:
            m["matched_keywords"] = json.loads(m["matched_keywords"] or "[]")
        score = conn.execute(
            "SELECT * FROM lead_scores WHERE lead_id = ?", (lead_id,)).fetchone()
        return {
            "lead_id": lead_id,
            "matches": matches,
            "best": dict(score) if score else None,
        }
    finally:
        conn.close()