"""Generate per-client business dossiers from matched leads.

Merges scraped detail (rating, reviews, hours, website, place_id) with the
matched solution + evidence and the outreach angle, then prints a human
readable dossier per lead (and writes it to an md file).

Usage (from repo root):
    python pipeline/lead_dossiers.py [--out pipeline/lead_dossiers.md] [--min-score 2]
"""

import argparse
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "crm.db"

SOLUTION_LABELS = {
    "lead-gen-automation": "Lead Generation Automation",
    "custom-web-application": "Custom Web Application",
    "realtime-tracking-dashboard": "Realtime Tracking Dashboard",
    "hiring-onboarding-platform": "Hiring & Onboarding Platform",
    "digital-presence-booking": "Website, Local SEO & Online Booking",
    "ai-powered-tools": "AI-Powered Tools",
    "inventory-stock-automation": "Inventory & Stock Automation",
    "billing-payments-automation": "Billing & Payments Automation",
    "retention-referral-loyalty": "Retention, Referral & Loyalty",
    "multi-location-ops": "Multi-Location Operations",
    "scheduling-rosters": "Scheduling & Rosters",
    "document-management": "Document Management",
    "customer-comms-automation": "Customer Communications Automation",
    "reports-dashboards": "Reports & Dashboards",
    "field-service-jobs": "Field Service & Jobs",
}


def parse_notes_extras(notes: str) -> dict:
    extras = {}
    if notes and "; " in notes:
        encoded = notes.split("; ", 1)[1]
        try:
            extras = json.loads(encoded)
        except (json.JSONDecodeError, IndexError):
            extras = {}
    return extras


def fetch_leads(conn: sqlite3.Connection, min_score: int):
    return conn.execute(
        """
        SELECT l.business_name, l.business_category, l.city, l.address_public,
l.website_url, l.public_business_phone, l.notes,
         l.booking_observation, l.conversion_observation,
         l.social_activity_observation,
         lm.solution_slug, lm.score, lm.matched_keywords, lm.evidence_note,
         lm.explanation, ls.tier, ls.total
        FROM lead_matches lm
        JOIN leads l ON l.lead_id = lm.lead_id
        JOIN lead_scores ls ON ls.lead_id = lm.lead_id
        WHERE lm.score >= ?
        ORDER BY ls.total DESC, lm.score DESC
        """,
        (min_score,),
    ).fetchall()


def format_dossier(rows):
    blocks = []
    for (name, category, city, address, website, phone, notes,
         booking_obs, conversion_obs, social_obs,
         slug, score, keywords, evidence, explanation, tier, total) in rows:
        extras = parse_notes_extras(notes)
        blocks.append(f"# {name}")
        meta = []
        if category:
            meta.append(f"Category: {category}")
        if city:
            meta.append(f"City: {city}")
        if address:
            meta.append(f"Address: {address}")
        if phone:
            meta.append(f"Phone: {phone}")
        if extras.get("rating"):
            meta.append(f"Rating: {extras['rating']} ({extras.get('reviews_count', '?')} reviews)")
        if website:
            meta.append(f"Website: {website}")
        if extras.get("hours"):
            meta.append(f"Hours: {json.dumps(extras['hours'], ensure_ascii=False)}")
        if extras.get("place_id"):
            meta.append(f"Place ID: {extras['place_id']}")
        blocks.append("\n".join(f"- {m}" for m in meta))
        blocks.append("")
        blocks.append(f"**Score**: {total} (tier {tier})")
        blocks.append(f"**Recommendation**: {SOLUTION_LABELS.get(slug, slug)} (match score {score})")
        if keywords:
            try:
                kw = ", ".join(json.loads(keywords))
            except json.JSONDecodeError:
                kw = str(keywords)
            blocks.append(f"**Evidence**: {kw}")
        if explanation:
            blocks.append(f"**Why**: {explanation}")
        if evidence:
            blocks.append(f"**Note**: {evidence}")
        obs = []
        if booking_obs:
            obs.append(booking_obs)
        if conversion_obs:
            obs.append(conversion_obs)
        if social_obs:
            obs.append(social_obs)
        if obs:
            blocks.append(f"**Observed problems**: {'; '.join(obs)}")
        blocks.append("")
    return "\n".join(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="pipeline/lead_dossiers.md")
    ap.add_argument("--min-score", type=int, default=1)
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    rows = fetch_leads(conn, args.min_score)
    doc = format_dossier(rows)

    out = Path(__file__).resolve().parent.parent / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {len(rows)} dossiers -> {out}")
    print()
    print(doc[:4000])


if __name__ == "__main__":
    main()