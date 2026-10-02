"""CLIENTFINDER - backfill html_body for drafts created before migration 0004.

Keeps existing draft IDs and statuses (no dupes, no churn). Rebuilds the HTML
alternative from the lead frame + the draft's own plain subject/body.

Usage:
  python pipeline/backfill_html_bodies.py            # all drafts missing html_body
  python pipeline/backfill_html_bodies.py --dry-run  # report only
"""
import argparse
import sqlite3
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent if "__file__" in locals() else Path(r"C:\Users\hsing\clientfinder-v3\pipeline")
ROOT = PIPE.parent
sys.path.insert(0, str(ROOT))

from client_framing import frame_lead  # noqa: E402
from html_email_builder import build_html_body  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    c = sqlite3.connect(str(PIPE / "crm.db"))
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "select d.id, d.subject, d.body, d.status, l.* from email_drafts d"
        " left join leads l on l.lead_id = d.lead_id"
        " where d.html_body is null or d.html_body = ''"
    ).fetchall()

    done = 0
    for r in rows:
        if not r["lead_id"] or not r["business_name"]:
            continue
        try:
            f = frame_lead(r)
        except Exception as e:
            print(f"skip draft {r['id']} (frame failed: {e})")
            continue
        email = r["public_business_email"] or ""
        try:
            html = build_html_body(f, r["subject"], r["body"], business_email=email)
        except Exception as e:
            print(f"skip draft {r['id']} (render failed: {e})")
            continue
        if args.dry_run:
            print(f"[dry] draft {r['id']} -> {len(html)} chars html")
        else:
            c.execute("update email_drafts set html_body=? where id=?", (html, r["id"]))
            c.commit()
            done += 1
            print(f"draft {r['id']} | html {len(html)} chars | {r['status']}")
    c.close()
    if args.dry_run:
        print(f"[dry-run] {len(rows)} drafts would be updated")
    else:
        print(f"updated html_body on {done} drafts")


if __name__ == "__main__":
    main()