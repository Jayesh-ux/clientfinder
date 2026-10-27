"""Export every lead to CSV with the derived lead_problem / why_they_pay_us columns.

Reads the CRM, writes <data>/outreach/all_leads_export.csv (override with --out).
The framing logic itself lives in pipeline/problem_framing.py, shared with
pipeline/infer_problems.py so the CSV and the stored columns never diverge.

Usage:
    python pipeline/update_problem_columns.py [--db PATH] [--out PATH]
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from problem_framing import lead_problem, lead_why  # noqa: E402
from service_catalog.config import OUTREACH_DIR, ensure_data_dirs, get_db_path  # noqa: E402

ap = argparse.ArgumentParser(description="Export leads CSV with derived problem framing.")
ap.add_argument("--db", default=None, help="CRM path (default: CLIENTFINDER_DB_PATH or pipeline/crm.db)")
ap.add_argument("--out", default=None, help="CSV output (default: data/outreach/all_leads_export.csv)")
args = ap.parse_args()

ensure_data_dirs()
DB = str(args.db) if args.db else str(get_db_path())
OUT = str(args.out) if args.out else str(OUTREACH_DIR / "all_leads_export.csv")

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute("select * from leads order by business_name").fetchall()
cols = [r[1] for r in c.execute("pragma table_info(leads)").fetchall()]
c.close()


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
NEW_COLS = ["lead_problem", "why_they_pay_us"]
out_cols = cols + NEW_COLS

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(out_cols)
    for r in rows:
        w.writerow([r[col] for col in cols] + [lead_problem(r), lead_why(r)])

print(f"updated {OUT} -> {len(rows)} rows, {len(out_cols)} cols")
print("\nsamples:")
for name in ["Sri Balaji Dental Studio", "Waves Gym", "32Smiles", "Home Makers Interior", "24 x 7 AC Repair"]:
    r = next((x for x in rows if x["business_name"].startswith(name)), None)
    if r:
        print(f"\n- {r['business_name']} [{r['business_category']}]")
        print(f"  PROBLEM: {lead_problem(r)}")
        print(f"  WHY PAY: {lead_why(r)}")