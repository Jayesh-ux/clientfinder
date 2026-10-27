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
  lead_problem / why_they_pay_us - derived framing (migration 0005), from
                               pipeline/problem_framing.py

Usage:
    python pipeline/infer_problems.py [--dry-run] [--all]

--all also frames leads that were not scraped from Google Maps (CSV imports,
seeded clinics). Framing is idempotent, so re-running is safe.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from problem_framing import lead_problem, lead_why  # noqa: E402
from service_catalog.config import get_db_path  # noqa: E402

DB_PATH = get_db_path()

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
    ap.add_argument("--all", action="store_true",
                    help="also frame every lead, not just scraped ones")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    where = "" if args.all else " WHERE source_type = 'google_maps_scrape'"
    rows = conn.execute(
        "SELECT * FROM leads" + where
    ).fetchall()

    has_framing = conn.execute(
        "SELECT 1 FROM pragma_table_info('leads') WHERE name = 'lead_problem'"
    ).fetchone() is not None

    changed = 0
    framed = 0
    for row in rows:
        updates = {}
        if not args.all and (row["website_status"] or "").lower() == "live":
            updates = infer_for(row)
            if not updates:
                continue
        elif args.all:
            updates = infer_for(row)

        if has_framing:
            updates["lead_problem"] = lead_problem(row)
            updates["why_they_pay_us"] = lead_why(row)

        if args.dry_run:
            print(f"# {row['lead_id'][:8]} : {updates}")
            continue
        if updates:
            sets = ", ".join(f"{k} = ?" for k in updates)
            conn.execute(
                f"UPDATE leads SET {sets} WHERE lead_id = ?",
                list(updates.values()) + [row["lead_id"]],
            )
            changed += 1
        if has_framing:
            framed += 1

    conn.commit()
    conn.close()
    verb = "would update (dry-run)" if args.dry_run else "updated"
    print(f"{verb}: {changed} leads")
    if has_framing:
        print(f"lead_problem / why_they_pay_us framed on {framed} leads")


if __name__ == "__main__":
    main()