"""Merge lead CSVs into the CRM, deduplicating by business identity.

Use this instead of a raw `import_leads.py` run when the source is an export
(`all_leads_export.csv`) or several overlapping scrapes. Those files carry one
`lead_id` per row, so the same business appears many times with different ids —
and every duplicate is a duplicate outreach target.

Identity is resolved in this order (first hit wins):
    1. Google place_id from the JSON embedded in `notes`
    2. public phone, normalised to the bare 10-digit NSN
    3. business name + address

When several rows share an identity the richest one wins (email present, then
most non-empty fields), and emails from the losing rows are merged in as
alternate contacts instead of being dropped.

Usage:
    python pipeline/merge_leads_csv.py FILE [FILE ...]
    python pipeline/merge_leads_csv.py data/raw/*.csv --dry-run
"""

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.scrape_to_leads import DEFAULT_COLUMNS as CSV_COLUMNS  # noqa: E402
from service_catalog.config import get_db_path  # noqa: E402

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
EXTRA_FIELDS = ["source_url", "instagram_url", "facebook_url", "contact_form_url",
                "decision_maker_name", "decision_maker_role"]


def parse_extras(notes):
    if not notes:
        return {}
    m = re.search(r"\{.*\}", notes, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except (json.JSONDecodeError, ValueError):
        return {}


def norm_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits.lstrip("0")


def identity_key(row):
    """Stable identity for a business, independent of the source file's ids."""
    place_id = (parse_extras(row.get("notes")).get("place_id") or "").strip()
    if place_id:
        return "gm_" + hashlib.sha1(place_id.encode("utf-8")).hexdigest()[:16]
    phone = norm_phone(row.get("public_business_phone"))
    if phone:
        return "gm_p" + hashlib.sha1(phone.encode("utf-8")).hexdigest()[:16]
    seed = f"{(row.get('business_name') or '').strip().lower()}|{(row.get('address_public') or '').strip().lower()}"
    return "gm_n" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def score(row):
    """Prefer the most contactable, most complete version of a business."""
    filled = sum(1 for v in row.values() if (v or "").strip())
    return (bool((row.get("public_business_email") or "").strip()),
            bool((row.get("public_business_phone") or "").strip()),
            bool((row.get("website_url") or "").strip()),
            filled)


def merge_group(rows):
    """Winner row + emails collected from every row in the group."""
    rows = sorted(rows, key=score, reverse=True)
    winner = dict(rows[0])
    emails = []
    for row in rows:
        email = (row.get("public_business_email") or "").strip().lower()
        if email and EMAIL_RE.match(email) and email not in emails:
            emails.append(email)
    if len(emails) > 1:
        winner["notes"] = (winner.get("notes") or "").rstrip("; ") + \
            f"; alt_emails={','.join(emails[1:])}"
    # keep any field the winner is missing but a sibling row had
    for row in rows[1:]:
        for field in EXTRA_FIELDS:
            if not (winner.get(field) or "").strip() and (row.get(field) or "").strip():
                winner[field] = row[field]
    return winner, len(rows)


def load(paths):
    merged = defaultdict(list)
    total = 0
    for path in paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row = {k: (row.get(k) or "").strip() if isinstance(row.get(k), str) else row.get(k)
                       for k in CSV_COLUMNS if k in row}
                merged[identity_key(row)].append(row)
                total += 1
    return merged, total


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+", help="lead CSV export(s) to merge")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    merged, total = load(args.files)
    groups = [(key, merge_group(rows)) for key, rows in merged.items()]
    collapsed = total - len(groups)
    print(f"read {total} rows -> {len(groups)} unique businesses "
          f"({collapsed} duplicate rows collapsed)")

    if args.dry_run:
        dupes = [(w.get('business_name'), n) for _, (w, n) in groups if n > 1]
        for name, n in sorted(dupes, key=lambda x: -x[1])[:15]:
            print(f"  {n}x {name}")
        return 0

    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    existing = {}
    for row in conn.execute("select lead_id, business_name, public_business_email,"
                            " public_business_phone, notes from leads"):
        existing[identity_key(dict(row))] = row["lead_id"]

    inserted = updated = 0
    for key, (winner, _n) in groups:
        winner["lead_id"] = key
        if key in existing:
            updated += 1
            continue
        cols = [c for c in CSV_COLUMNS if c != "lead_id"]
        placeholders = ",".join("?" * (len(cols) + 1))
        conn.execute(
            f"INSERT INTO leads (lead_id,{','.join(cols)}) VALUES ({placeholders})",
            [key] + [winner.get(c, "") for c in cols],
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"inserted {inserted}, already present {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())