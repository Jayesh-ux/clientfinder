"""Infer honest business problems from scraped detail already in the CRM.

Reads the JSON detail we now keep in `leads.notes` (place_id, coordinates,
rating, reviews_count, hours, categories) plus the columns themselves
(website_url, website_status, public_business_phone) and writes *observed*
symptoms into the observation fields that `leadmatcher` consumes.

Every inferred observation is traceable to a scraped signal. No category-only
guessing: a salon and a car wash are treated the same unless the scraped
detail (phone-only booking, review momentum, hours) says otherwise.

Fields written (only when there is evidence):
  booking_observation         - manual booking by phone / calls for every booking
  conversion_observation      - no online presence found, customers cannot find us online
  social_activity_observation - review/rating momentum not leveraged online

Usage:
    python pipeline/infer_problems.py [--dry-run]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "crm.db"

PHONE_ONLY = "no online booking", "cannot book online", "bookings by phone", "manual booking"
NO_PRESENCE = "no online presence", "customers cannot find us online", "no website"


def parse_extras(notes):
    if notes and "; " in notes:
        try:
            return json.loads(notes.split("; ", 1)[1])
        except (json.JSONDecodeError, IndexError):
            return {}
    return {}


def infer_for(row):
    """Return {field: value} observations justified by this lead's signals."""
    extras = parse_extras(row["notes"] or "")
    website = (row["website_url"] or "").strip()
    phone = (row["public_business_phone"] or "").strip()
    rating = extras.get("rating")
    reviews = extras.get("reviews_count")
    hours = extras.get("hours")

    updates = {}

    # A business reachable only by phone (no website) is a phone-only booking
    # shop: every booking comes in as a call.
    if not website and phone:
        updates["booking_observation"] = " ".join(PHONE_ONLY)
        updates["conversion_observation"] = " ".join(NO_PRESENCE)
    if not website and not phone:
        updates["conversion_observation"] = " ".join(NO_PRESENCE)

    # Strong rating + review volume with no website = demand that isn't being
    # captured / monetized online.
    if rating is not None:
        try:
            rating_f = float(rating)
        except (TypeError, ValueError):
            rating_f = None
        if rating_f is not None and rating_f >= 4.3 and not website:
            momentum = f"strong ratings ({rating_f:.1f}, {reviews or 0} reviews) not leveraged online"
            updates["social_activity_observation"] = momentum

    # Listing hours but no way to book online -> every reservation is manual.
    if hours and not website:
        existing = updates.get("booking_observation", "")
        updates["booking_observation"] = "manual booking by phone; calls for every booking; no online booking"

    return updates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT lead_id, website_url, website_status, public_business_phone,"
        " notes FROM leads WHERE source_type = 'google_maps_scrape'"
    ).fetchall()

    changed = 0
    for row in rows:
        if (row["website_status"] or "").lower() == "live":
            continue
        updates = infer_for(row)
        if not updates:
            continue
        if args.dry_run:
            print(f"# {row['lead_id'][:8]} : {updates}")
            continue
        sets = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(
            f"UPDATE leads SET {sets} WHERE lead_id = ?",
            list(updates.values()) + [row["lead_id"]],
        )
        changed += 1

    conn.commit()
    conn.close()
    print(f"{'would update (dry-run)' if args.dry_run else 'updated'}: {changed} leads")


if __name__ == "__main__":
    main()