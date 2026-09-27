# Google Maps Scraper API

A FastAPI service for scraping Google Maps data based on search queries. Ideal for n8n users.

Very high performance, watch out for rate limiting!

Use variables to replace URL parameters

scrape-get?query=hotels%20in%2098392&max_places=100&lang=en&headless=true"

If using n8n or other automation, use the /scrape-get endpoint for it to return results

simple install, copy files and run docker compose up -d

Intened to be used with this n8n build:
https://github.com/conor-is-my-name/n8n-autoscaling

## Recent Updates

### February 2026 - Stability Refactor ✨
- **Major extractor refactoring** for long-term reliability
  - Prioritizes semantic HTML attributes (aria-labels, data-item-id) over fragile CSS classes
  - Significantly more resistant to Google Maps interface updates
- **New field**: `hours` - Extracts business hours by day
- **Improved category filtering** - Removes UI noise from categories
- See [DATA_EXTRACTION_ANALYSIS.md](DATA_EXTRACTION_ANALYSIS.md) for technical details 

## API Endpoints

### POST `/scrape`
Main endpoint for scraping Google Maps data (accepts JSON body)

### GET `/scrape-get`
Alternative GET endpoint with query parameters (recommended for n8n and webhooks)

### GET `/`
Health check endpoint

## API Parameters

All endpoints support the same parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | **Yes** | - | Search query (e.g., "hotels in 98392", "restaurants near Times Square") |
| `max_places` | integer | No | `null` | Maximum number of results to return. If not set, returns all found results |
| `lang` | string | No | `"en"` | Language code for results. Supports: `en`, `es`, `fr`, `de`, `pt`, and more |
| `headless` | boolean | No | `true` | Run browser in headless mode. Set to `false` for debugging |
| `concurrency` | integer | No | `5` | Number of concurrent browser tabs for scraping (range: 1-20). Higher = faster but more detection risk |

### Parameter Notes
- **query**: URL encode special characters when using GET endpoint
- **max_places**: Useful for limiting API costs and response time. Without this, the scraper will continue until all results are found or the end of the list is reached
- **lang**: Affects both the language of results and consent form detection
- **headless**: Set to `false` only for local debugging (not recommended in Docker)
- **concurrency**: Default of 5 is balanced. Increase for speed (max 10 recommended) or decrease to 1-2 if experiencing rate limiting

## Example Requests

### POST Example
```bash
curl -X POST "http://localhost:8001/scrape" \
-H "Content-Type: application/json" \
-d '{
  "query": "hotels in 98392",
  "max_places": 10,
  "lang": "en",
  "headless": true,
  "concurrency": 5
}'
```

### GET Example (URL encoded)
```bash
curl "http://localhost:8001/scrape-get?query=hotels%20in%2098392&max_places=10&lang=en&headless=true&concurrency=5"
```

### Using with Docker service name
```bash
curl "http://gmaps_scraper_api_service:8001/scrape-get?query=coffee%20shops%20in%20seattle&max_places=50&lang=en"
```

### Scraping all results (no limit)
```bash
curl "http://localhost:8001/scrape-get?query=restaurants%20in%20miami&lang=en"
```

### Spanish language results
```bash
curl "http://localhost:8001/scrape-get?query=restaurantes%20en%20barcelona&max_places=20&lang=es"
```

### High-speed scraping (increased concurrency)
```bash
curl -X POST "http://localhost:8001/scrape" \
-H "Content-Type: application/json" \
-d '{
  "query": "gyms in los angeles",
  "max_places": 100,
  "lang": "en",
  "headless": true,
  "concurrency": 10
}'
```



## Running the Service

### Docker
```bash
docker-compose up --build
```

### Local Development
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API:
```bash
uvicorn gmaps_scraper_server.main_api:app --reload
```


The API will be available at `http://localhost:8001`

or for docker:

`http://gmaps_scraper_api_service:8001`

## Response Format

Each place in the results includes:

```json
{
  "name": "Starbucks",
  "place_id": "ChIJ...",
  "coordinates": {
    "latitude": 47.6062,
    "longitude": -122.3321
  },
  "address": "1912 Pike Pl, Seattle, WA 98101",
  "rating": 4.3,
  "reviews_count": 1234,
  "reviews_url": "https://search.google.com/local/reviews?placeid=...",
  "categories": ["Coffee shop", "Cafe"],
  "website": "https://www.starbucks.com",
  "phone": "2066241965",
  "hours": ["Monday, 5 AM to 9 PM", "Tuesday, 5 AM to 9 PM"],
  "thumbnail": "https://...",
  "link": "https://www.google.com/maps/place/..."
}
```

### Field Notes

- **`rating`**: Overall rating (1.0-5.0), extracted using stable accessibility attributes
- **`reviews_count`**: Total number of reviews (numeric count)
- **`hours`**: Business hours by day (e.g., "Monday, 5 AM to 9 PM") - extracted when available
- **`reviews_url`**: ⚠️ **DEPRECATED** - This URL format no longer works and returns 404 errors as of 2026
- **Individual review extraction**: ⚠️ **Not supported** - Google requires user authentication to view full review content. The scraper can extract overall ratings and review counts but cannot access individual review text/data

### Extraction Stability (Updated Feb 2026)

The scraper has been refactored to prioritize **stable, semantic selectors** over fragile CSS classes:

- 🟢 **Highly Stable Fields**: Use accessibility attributes (`aria-label`, `data-item-id`) that are unlikely to break
  - Address, phone, website, rating, hours, name, place_id
- 🟡 **Moderately Stable**: Use common text patterns
  - Reviews count, categories
- See [DATA_EXTRACTION_ANALYSIS.md](DATA_EXTRACTION_ANALYSIS.md) for technical details

## Features

- ⚡ **Parallel processing**: Scrapes multiple places concurrently (configurable with `concurrency` parameter)
- 📊 **Comprehensive data**: Name, rating, review count, address, coordinates, phone, website, categories, hours, and more
- 🌍 **Multi-language support**: Works with en, es, fr, de, pt, and more
- 🛡️ **Anti-detection**: Random delays and user agent rotation to avoid rate limiting
- 🔄 **Robust error handling**: Multiple fallback strategies for consent forms and feed detection
- 🎯 **Stability-first extraction**: Prioritizes semantic HTML attributes (aria-labels, data-item-id) over fragile CSS classes for long-term reliability

## Troubleshooting

### "Feed element not found" error
- This usually means Google Maps changed its DOM structure or no results were found
- The scraper now has multiple fallback strategies to handle this
- Try with a different query or language parameter

### Empty results
- Check that your query returns results on Google Maps directly
- Try with `headless=false` to see what the browser is doing
- Check Docker logs: `docker logs gmaps_scraper_api_service`

### Slow performance
- Adjust the `concurrency` parameter (higher = faster but more detection risk)
- Default is 5 concurrent tabs, max recommended is 10
- Random delays are added for anti-detection (1-2 seconds per scroll)

### Language-specific issues
- Consent forms are now supported in: en, es, fr, de, pt, and more
- Use the `lang` parameter to match your target region
- Example: `lang=es` for Spanish results

## Notes
- For production use, consider adding authentication
- The scraping process may take several seconds to minutes depending on the number of results
- Recommended rate limiting: Max 500 places/day per IP, min 60s between API calls
- Use the `concurrency` parameter to tune performance vs. detection risk (default: 5)

## Known Limitations

- **Review extraction not supported**: Google Maps requires user authentication (login) to view full review content. As of 2026, individual reviews cannot be scraped without violating Google's Terms of Service. The scraper can still extract:
  - Overall rating (e.g., 4.3 stars)
  - Total review count (e.g., 1,234 reviews)
  - Place metadata (name, address, phone, website, etc.)
- **Reviews URL deprecated**: The `reviews_url` field returns a URL that no longer works (404 error) as of 2026
- For alternatives, consider using Google's official Places API for review access (requires API key and has usage costs)
# google-map-scraper

## CLIENTFINDER v3: Dynamic Capability Catalog

CLIENTFINDER v3 adds a flexible, dynamic capability catalog to the existing scraper + CRM pipeline. It maps business problems to candidate solutions using skills and verified portfolio evidence — **without** locking you into predefined service categories.

> **Validation status:** the full loop has been proven end-to-end — see
> "Proven end-to-end" below. What's more, **matching is now need-driven and
> niche-agnostic**: only observed symptoms (no website, phone-only booking,
> attendance gaps, manual stock, …) select the offering. Full test suite: **31/31 passing**.

### Quick start (local)

Requires Python 3.11+ and the deps in `requirements-dev.txt`. Browsers for the
scraper are handled automatically: on Windows it prefers an installed
Chrome/Edge, else `python -m playwright install chromium`.

```bash
# 1. Apply migrations + seed the catalog (creates/upgrades pipeline/crm.db)
python pipeline/migrate.py --seed

# 2. Scrape real prospects from Google Maps (offline-friendly, headless)
python pipeline/run_scrape.py "dental clinic near me" --max 20 --out pipeline/leads_scraped.json

# 3. Bridge scrape JSON -> v2 leads CSV -> import into pipeline/crm.db
python pipeline/scrape_to_leads.py pipeline/leads_scraped.json    # run from pipeline/

# 4. Match every lead against the catalog (need-driven)
cd pipeline && python match_leads.py

# 5. Run the API (catalog + offerings + existing scrape endpoints on :8001)
uvicorn gmaps_scraper_server.main_api:app --reload
```

### Quick start (Docker-based validation)

```bash
docker build -f Dockerfile.test -t clientfinder-test .
docker run --rm clientfinder-test        # runs pytest suite
```

### Key ideas

- **capabilities** — skills/capabilities with a `verification_level`
  (`verified_industry` | `verified_project` | `familiarity` | `unvalidated`) so
  nothing is over-claimed.
- **portfolio_evidence** — real projects with provenance + verified flag; only
  the current repository is auto-marked verified.
- **solution_templates** — reusable "what I can build" blueprints composed of
  capabilities + evidence.
- **problem_patterns** — business pain points with match keywords mapped to
  solution templates. The `/catalog/match` endpoint discovers candidates from
  free text (lead context, business description, chat message).
- Fully customizable: add capabilities/solutions/patterns via the API.

### Catalog API (mounted under `/catalog`)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/catalog/capabilities` | list capabilities |
| POST | `/catalog/capabilities` | add capability |
| GET | `/catalog/match?text=...` | match business problem → solutions |
| GET/POST | `/catalog/evidence` | portfolio evidence |
| GET/POST | `/catalog/solutions` | solution templates |
| GET/POST | `/catalog/patterns` | problem patterns |

Each resource also supports `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`.

### Example match

```bash
curl "http://localhost:8001/catalog/match?text=part%20of%20the%20team%20is%20remote%20on%20site%20and%20we%20need%20attendance%20and%20time%20tracking"
```

Returns ranked solution templates (e.g. `realtime-tracking-dashboard`) with the
capability slugs and evidence behind each match. Add `&include_score=true` to
attach a fit-scorecard (`need_fit`, `scale_fit`, `urgency`,
`evidence_confidence`, total + tier) to each candidate.

### Match CRM leads against the catalog

```bash
# Matches every lead in pipeline/crm.db -> writes lead_matches + lead_scores
python pipeline/match_leads.py

# One lead, dry-run (compute only, no writes)
python pipeline/match_leads.py --lead-id lead-abc --dry-run
```

API equivalents: `GET /catalog/leads/{lead_id}/match` and
`GET /catalog/leads/{lead_id}/matches`. The v2 `leads` table is **never
modified** — matches/scores land in the additive 0002 tables.

### Offerings & outreach (what we can actually sell)

`service_catalog/offerings.py` is the "sellable" layer: each catalog solution
gets a concrete **gig** (deliverables), a **SaaS variant**, and a
**personalized outreach draft** (angle + openers + hooks). It is
niche-agnostic by design — mapped to symptoms, not industries.

- `GET /offerings` — full list (15 offerings) with deliverables + SaaS angles.
- `GET /offerings/{slug}` — the angle/template for one offering.
- `GET /offerings/{slug}/draft?business=...&area=...` — **DRAFT ONLY** outreach
  body for a specific prospect, with high-entropy variation (each render picks a
  different opener/hook combo) to avoid message fingerprinting.
- Nothing served under `/offerings` ever sends anything.

```bash
curl "localhost:8001/offerings/inventory-stock-automation/draft?business=Acme%20Store&area=Delhi"
curl localhost:8001/offerings
```

Offering coverage is intentionally broad so "what we can sell" stays open:
lead-gen automation, digital presence + booking, custom web apps, hiring/
onboarding platforms, AI-assisted tools, inventory automation, billing/payments,
retention & referrals, multi-location ops, scheduling/rosters, document
management, customer-comms automation, reports/dashboards, field-service jobs,
and realtime tracking dashboards.

### Proven end-to-end (offline demo)

The complete client-finder loop has been exercised against real modules and a
real `pipeline/crm.db`:

1. **Scrape** — a live headless scrape of `"dental clinic near me"` via
   `pipeline/run_scrape.py` returned 5 real Pune clinics (name, category,
   website, phone, address, rating, review count) and saved them to
   `pipeline/leads_scraped.json`. `gmaps_scraper_server.extractor` runs on
   the live page; earlier, it was also proven standalone on a saved HTML sample.
2. **Import** — records from both the live scrape (5 clinics) and the earlier
   sample page became leads via `pipeline/scrape_to_leads.py`
   (scrape JSON → v2 CSV) then `pipeline/import_leads.py` into the `leads`
   table (8 businesses total: dental clinics, salon, interior studio, cafe,
   construction — a deliberately cross-niche mix).
3. **Catalog** — `pipeline/migrate.py --seed` applied the 0001–0003 migrations
   and seeded capabilities/solutions/patterns (with provenance tiers).
4. **Match & score** — `pipeline/match_leads.py` matched all leads with
   observable symptoms and wrote `lead_matches` + `lead_scores`. Cross-niche
   proof: construction site with attendance gaps matched
   `realtime-tracking-dashboard`; a lead with no website matched
   `digital-presence-booking`; stock problems matched inventory automation —
   always the right offering for the **symptom**, never the niche. Every match
   carries a readable `explanation`.
5. **Draft** — personalized outreach drafts were generated per matched lead from
   `service_catalog/offerings.render_outreach` (business name + area injected,
   varied openers/hooks). Sending was refused until (a) approved by an operator
   AND (b) the account had `send_enabled=1`; the final refusal was DNS on a fake
   SMTP host, never a bypass. Inbound stays read-only and draft-only.
6. **Serve** — `uvicorn gmaps_scraper_server.main_api:app` booted cleanly with
   the catalog mounted; `GET /catalog/match` returned the correct top solution.

### Email subsystem (draft-only by default)

Safety contract: **nothing is ever sent automatically.** A draft must be
`approved` by an operator AND the linked account must have `send_enabled=1`;
credentials come from the environment (`CF_SMTP_PASSWORD`, `CF_IMAP_PASSWORD`)
and are never stored in the repo or DB.

```bash
# accounts
curl -X POST localhost:8001/email/accounts \
  -d '{"name":"Work","smtp_host":"smtp.example.com","smtp_port":587,"smtp_user":"me@x.com","from_email":"me@x.com","imap_host":"imap.example.com","imap_port":993,"imap_user":"me@x.com"}'
curl -X POST "localhost:8001/email/accounts/1/enable?enabled=true"

# drafts
curl -X POST localhost:8001/email/drafts -d '{"subject":"Hi","body":"...","account_id":1}'
curl -X POST localhost:8001/email/drafts/bulk -d '{"items":[...]}'
curl -X POST localhost:8001/email/drafts/1/approve
curl -X POST localhost:8001/email/drafts/1/send      # refuses until enabled

# inbound (never auto-replies)
curl -X POST localhost:8001/email/inbox/pull?account_id=1
curl localhost:8001/email/inbox
```

See [CLIENTFINDER_V3_PHASE0_INSPECTION.md](CLIENTFINDER_V3_PHASE0_INSPECTION.md)
for the full Phase 0 report (architecture, dependency map, migration plan,
implementation sequence, risk register).
