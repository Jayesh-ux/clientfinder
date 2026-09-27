"""Dynamic business-problem -> solution matching for CLIENTFINDER v3.

Phase-3-lite: maps free text (lead context, business description, chat message)
to candidate solution templates by detecting problem patterns, then surfaces the
capabilities and verified evidence behind each match. Extensible to LLM-based
matching later.
"""

import json
import re

from service_catalog.db import connect
from service_catalog.repository import get_solution


def _patterns():
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT p.*, s.slug AS solution_slug FROM problem_patterns p"
            " JOIN solution_templates s ON s.id = p.solution_id"
            " WHERE p.is_active = 1").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["keywords"] = json.loads(d["keywords"] or "[]")
            out.append(d)
        return out
    finally:
        conn.close()


def _tokenize(text):
    text = (text or "").lower()
    tokens = set(re.findall(r"[a-z0-9]+", text))
    phrases = set()
    words = re.findall(r"[a-z0-9']+", text)
    for n in (2, 3):
        phrases.update(" ".join(words[i:i + n]) for i in range(len(words) - n + 1))
    return tokens, phrases


def _keyword_hits(keywords, tokens, phrases):
    hits = []
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in phrases or kw_lower in tokens:
            hits.append(kw_lower)
    return hits


def match_business_problem(text, top_k=5, min_score=1):
    """Return ranked candidate solutions for a business-problem description.

    Each result: solution (hydrated), matched_patterns, score (hit count),
    and evidence/capability provenance.

    A pattern only counts as evidence if it produced a *specific* hit: either a
    multi-word keyword (phrase) or at least two distinct single keywords. A lone
    generic word must never trigger a match.
    """
    tokens, phrases = _tokenize(text)
    scored = {}

    for pat in _patterns():
        hits = _keyword_hits(pat["keywords"], tokens, phrases)
        phrase_hits = [h for h in hits if " " in h]
        if phrase_hits:
            weight = 2 * len(phrase_hits) + len([h for h in hits if " " not in h])
        elif len(hits) >= 2:
            weight = len(hits)
        else:
            continue
        scored.setdefault(pat["solution_slug"], {
            "matches": [], "score": 0, "pattern_ids": [],
        })
        scored[pat["solution_slug"]]["matches"].append(hits)
        scored[pat["solution_slug"]]["score"] += weight
        scored[pat["solution_slug"]]["pattern_ids"].append(pat["id"])

    results = []
    for slug, agg in sorted(scored.items(), key=lambda kv: kv[1]["score"], reverse=True):
        if agg["score"] < min_score:
            continue
        sol = get_solution_by_slug(slug)
        if not sol or not sol.get("is_active", True):
            continue
        verified = [e for e in sol.get("evidence", []) if e.get("verified")]
        matched_kw = [kw for group in agg["matches"] for kw in group]
        results.append({
            "solution": sol,
            "match_score": agg["score"],
            "matched_keywords": matched_kw,
            "pattern_ids": agg["pattern_ids"],
            "evidence_note": (
                "verified" if verified else
                "none-verified" if sol.get("evidence") else "none"),
            "explanation": (
                f"Lead text mentions: {', '.join(sorted(set(matched_kw))[:4])}. "
                f"Suggested solution: {sol['name']}."),
        })
        if len(results) >= top_k:
            break
    return results


def get_solution_by_slug(slug):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM solution_templates WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            return None
        return get_solution(row["id"])
    finally:
        conn.close()