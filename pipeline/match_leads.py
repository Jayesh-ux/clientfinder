"""CLIENTFINDER v3: match leads in the CRM against the capability catalog.

Additive to the v2 pipeline. Reads FROM the `leads` table, writes matches and
scores INTO lead_matches / lead_scores (created by migration 0002). The leads
table itself is never modified.

Usage:
    python pipeline/match_leads.py [--top-k 5] [--min-score 1] [--limit N]
                                   [--dry-run] [--lead-id <id>]
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from service_catalog.leadmatcher import for_lead, get_stored_matches, match_all


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=int, default=1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="compute matches but do not persist")
    parser.add_argument("--lead-id", type=str, default=None,
                        help="match a single lead id instead of all")
    args = parser.parse_args(argv)

    persist = not args.dry_run

    if args.lead_id:
        results = for_lead(args.lead_id, top_k=args.top_k,
                           min_score=args.min_score, persist=persist)
        if results is None:
            print(f"Lead not found: {args.lead_id}")
            return 1
        for item in results:
            print(f"  {item['solution']['slug']:30s} "
                  f"match={item['match_score']:2d} "
                  f"score={item['score']['total']:3d} "
                  f"tier={item['score']['tier']}")
        print(json.dumps(get_stored_matches(args.lead_id),
                         indent=2, default=str))
        return 0

    summary = match_all(top_k=args.top_k, min_score=args.min_score,
                        limit=args.limit, persist=persist)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())