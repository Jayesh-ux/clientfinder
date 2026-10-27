"""Paced sender for approved client-outreach drafts (Gmail API / OAuth2).

AGENTS.md requires: no identical-blast fingerprinting, rate limiting, and an
immediate halt on any platform warning or restriction. This runner enforces all
three:

  - Each message already carries per-lead copy (different business, category,
    offer and dates), so there is no template fingerprint to vary here.
  - --interval seconds between sends with +/- 40% jitter, so the pattern is not
    metronomic. Defaults are deliberately slow for a personal account.
  - HARD HALT on quota / policy / auth errors: any response whose error text
    looks like a Gmail restriction stops the run immediately rather than
    burning the rest of the batch and getting the account flagged.

Nothing here approves drafts - approval stays an operator action. This only
walks drafts already at status='approved' with send_enabled=1.

Usage:
    python pipeline/send_approved.py            # paced send, defaults
    python pipeline/send_approved.py --limit 5
    python pipeline/send_approved.py --dry-run
"""

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service_catalog.db import connect, row_to_dict  # noqa: E402
from service_catalog.email import send_draft_gmail  # noqa: E402

# Any of these in an error string means Gmail is warning or restricting us.
# AGENTS.md: halt immediately and alert the operator.
HALT_MARKERS = (
    "429", "quota", "rate limit", "ratelimit", "too many",
    "550", "551", "552", "553", "blocked", "blacklist", "blocklisted",
    "policy", "spam", "suspicious", "unusual", "quotaexceeded",
    "403", "401", "invalid_grant", "disabled",
)


def looks_like_restriction(err):
    if not err:
        return False
    low = str(err).lower()
    return any(marker in low for marker in HALT_MARKERS)


def pending_drafts():
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT d.id, d.subject, l.business_name, l.public_business_email"
            " FROM email_drafts d"
            " JOIN leads l ON l.lead_id = d.lead_id"
            " WHERE d.status = 'approved'"
            "   AND l.public_business_email != ''"
            "   AND COALESCE(l.do_not_contact, 0) = 0"
            " ORDER BY d.id"
        ).fetchall()
    finally:
        conn.close()
    return [row_to_dict(r) for r in rows]


def main():
    ap = argparse.ArgumentParser(description="Send approved drafts, paced + fail-safe")
    ap.add_argument("--limit", type=int, default=0, help="stop after N sends (0 = all)")
    ap.add_argument("--interval", type=float, default=18.0,
                    help="base seconds between sends (jittered +/-40%%)")
    ap.add_argument("--max-interval", type=float, default=45.0,
                    help="never sleep longer than this")
    ap.add_argument("--dry-run", action="store_true", help="list what would send, send nothing")
    args = ap.parse_args()

    queue = pending_drafts()
    print(f"[queue] {len(queue)} approved draft(s) ready")
    if not queue:
        return 0

    if args.dry_run:
        for d in queue[: args.limit or None]:
            print(f"  would send #{d['id']} -> {d['public_business_email']} | {d['subject'][:60]}")
        print(f"[dry-run] {min(args.limit or len(queue), len(queue))} message(s) not sent")
        return 0

    sent = failed = 0
    halted_reason = None

    for i, d in enumerate(queue, 1):
        if args.limit and sent >= args.limit:
            break

        res = send_draft_gmail(d["id"])
        if res.get("sent"):
            sent += 1
            print(f"[{i}/{len(queue)}] SENT #{d['id']} -> {d['public_business_email']}"
                  f" | {d['subject'][:55]}", flush=True)
        else:
            err = res.get("error") or ""
            failed += 1
            print(f"[{i}/{len(queue)}] FAIL #{d['id']} -> {d['public_business_email']}"
                  f" | {err[:160]}", flush=True)
            if looks_like_restriction(err):
                halted_reason = err
                print(f"\n[HALT] platform restriction detected - stopping the run "
                      f"immediately per AGENTS.md.", flush=True)
                print(f"[HALT] reason: {err[:300]}", flush=True)
                break

        # Skip the trailing sleep when we know we are about to stop.
        if i < len(queue) and not (args.limit and sent >= args.limit) and not halted_reason:
            delay = max(4.0, min(args.max_interval, args.interval * random.uniform(0.6, 1.4)))
            time.sleep(delay)

    print(f"\n[done] sent={sent} failed={failed} remaining={len(queue) - sent - failed}")
    if halted_reason:
        print("[action] do not retry until the restriction clears; check the account.")
        return 2
    if failed:
        print("[action] review failures before the next batch.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
