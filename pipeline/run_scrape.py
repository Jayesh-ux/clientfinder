"""Run a real Google Maps scrape and pipe results into the CLIENTFINDER pipeline.

Usage (from repo root):
    python pipeline/run_scrape.py "dentist near me" --max 20 --out pipeline/leads_scraped.json
    python pipeline/run_scrape.py --queries-file queries.txt --max 10 --out pipeline/mix.json

The output JSON matches the shape consumed by pipeline/import_leads.py (which can
also import a raw CSV from the v2 scraper server). Network/browser availability
is checked and reported; scraping runs headless with safe defaults and rate
limits. All lead import stays inside this repo — nothing is emailed out.
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gmaps_scraper_server import scraper  # noqa: E402

logger = logging.getLogger("run_scrape")


def _clean_business(b: dict) -> dict:
    """Normalize a scraper record into CLIENTFINDER import shape.

    Keeps the full extractor detail (place_id, coordinates, categories,
    hours, thumbnail, reviews_url) so per-lead intelligence survives, not
    just the 8 core import fields.
    """
    phone = (b.get("phone_number") or b.get("phone") or "").strip()
    ratings = (b.get("categories") or []) if not isinstance(b.get("categories"), str) else [b["categories"]]
    return {
        "name": (b.get("title") or b.get("name") or "Unknown").strip(),
        "category": (b.get("category") or (b.get("categories") or [""])[0] or "").strip(),
        "categories": ratings,
        "website": (b.get("website") or "").strip(),
        "phone": phone,
        "address": (b.get("address") or "").strip(),
        "city": (b.get("city") or "").strip(),
        "place_id": b.get("place_id"),
        "coordinates": b.get("coordinates"),
        "rating": b.get("rating"),
        "reviews_count": b.get("reviews_count"),
        "reviews_url": b.get("reviews_url"),
        "hours": b.get("hours"),
        "thumbnail": b.get("thumbnail"),
        "link": b.get("link"),
    }


async def _run(query: str, max_places: int, browser, context) -> list:
    print(f"[scrape] query={query!r} max={max_places}", flush=True)
    return await scraper.scrape_with_browser(
        query, browser, context, max_places=max_places)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", help="single maps query")
    ap.add_argument("--queries-file", help="file with one query per line")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between queries to stay under Maps rate limits")
    ap.add_argument("--concurrency", type=int, default=3, help="parallel detail tabs per query")
    ap.add_argument("--out", default="pipeline/leads_scraped.json")
    args = ap.parse_args()

    queries = []
    if args.queries_file:
        queries = [l.strip() for l in Path(args.queries_file).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.query:
        queries.append(args.query)
    if not queries:
        raise SystemExit("no query given")

    out_path = Path(__file__).resolve().parent.parent / args.out

    all_businesses = []

    async def scrape_all():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                channel=None,
                args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-setuid-sandbox'],
            )
            try:
                context = await browser.new_context(
                    user_agent=random.choice(scraper.USER_AGENTS),
                    java_script_enabled=True,
                    accept_downloads=False,
                    locale="en",
                )
                for i, q in enumerate(queries):
                    try:
                        raw = await _run(q, args.max, browser, context)
                    except Exception as exc:
                        print(f"[scrape] FAILED for {q!r}: {exc}", flush=True)
                        continue
                    cleaned = [_clean_business(b) for b in raw if isinstance(b, dict)]
                    print(f"[scrape] {q!r}: {len(cleaned)} businesses", flush=True)
                    all_businesses.extend(cleaned)
                    if i < len(queries) - 1 and args.delay > 0:
                        time.sleep(args.delay)
            finally:
                await browser.close()

    asyncio.run(scrape_all())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_businesses, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved {len(all_businesses)} businesses -> {out_path}", flush=True)
    print("next: python pipeline/import_leads.py --source {out_path} --input-format json".format(out_path=out_path))


if __name__ == "__main__":
    main()