# CLIENTFINDER v3 — Phase 0 Inspection Report

- Prepared by: Coding agent (machine: Windows, user `hsing`)
- Scope: Enablement, not implementation. This report precedes Phase 1+ coding.
- Source repo: `https://github.com/Rohitjaiswar123/google-map-scraper` (CLIENTFINDER v2 baseline)
- Copy at: `C:\Users\hsing\clientfinder-v3`

---

## 1. Repository Inventory

```
clientfinder-v3/
├── AGENTS.md                # OpenCode agent rules (anti-duplication + anti-spam). KEEP as-is.
├── README.md                # Project overview, Quick Start, API reference
├── requirements.txt         # playwright, fastapi, uvicorn[standard], graphifyy
├── setup.py                 # py pkg `gmaps_scraper_server` v0.1
├── Dockerfile               # python:3.10-slim, port 8001, Playwright browsers, `uvicorn main_api:app`
├── docker-compose.yml       # 3 services: scraper-api, postgres (gmaps_leads), n8n
├── .gitignore               # excludes .env, crm.db, scratch/, queues, csvs
├── LICENSE
├── gmaps_scraper_server/
│   ├── __init__.py
│   ├── main_api.py          # FastAPI app, 2 endpoints: GET /scrape-get, POST /scrape
│   ├── scraper.py           # Playwright-based Google Maps scraper (async browser)
│   └── extractor.py         # HTML DOM extraction, stability-prioritized regexes
├── pipeline/                # SQLite CRM pipeline (v2 "secret sauce") — LOCAL ONLY
│   ├── init_db.py           # creates crm.db schema (leads, fields, interactions)
│   ├── import_leads.py      # CSV scrapes -> leads table (dedup by place_id/phone)
│   ├── seed_new_leads.py    # initial lead seeding from scratch CSV outp
│   ├── draft_messages.py    # personalized WhatsApp message drafts
│   ├── daily_queue.py       # rates lead queue processing per day
│   ├── update_status.py     # status transitions (new -> queued -> sent -> replied -> won)
│   └── update_phones.py     # phone enrichment/cleanup
├── n8n-node/
│   └── json.json            # n8n workflow: trigger -> code -> scrape API -> postgres
└── docs/                    # README, PIPELINE_BRIEF, REFACTORING_SUMMARY,
                             #   DATA_EXTRACTION_ANALYSIS, leads schema, + Graphify autogen
```

Note: `crm.db`, `.env`, outbound scripts (`whatsapp_*.js`, `orchestrate_campaign.js`, `lead_analyzer.js`) and credentials were **removed from the repo** (only docs/ of them remain). The outreach/DM logic is documented in `docs/PIPELINE_BRIEF.md` and `docs/README.md`. Behavior must be reconstructed from docs, not code.

---

## 2. Architecture Diagram (v2, as deployed)

```
                        ┌───────────────────────────────────────────────┐
                        │                 USER (operator)                │
                        │   runs n8n OR hits API directly                │
                        └──────────────┬────────────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────┐
                    │  n8n workflow (n8n-node/json.json)  │
                    │  trigger -> code -> HTTP -> postgres │
                    └──────────────────┬──────────────────┘
                                       │ http://scraper-api:8001
                    ┌──────────────────▼──────────────────┐
                    │    gmaps_scraper_server API (:8001) │  FastAPI
                    │   GET /scrape-get  POST /scrape     │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐      ┌──────────────────┐
                    │   scraper.py (Playwright)   │      │  extractor.py    │
                    │   async browser, stealth    │──────│  DOM extraction  │
                    │   pagination, radial caps   │      │  (stability ▶▶)  │
                    └─────────────────────────────┘      └──────────────────┘
                                   │
                          raw JSON scrapes (CSV/JSON)
                                   │
                    ┌──────────────▼──────────────────────────────┐
                    │              PIPELINE (SQLite)              │
                    │  import_leads ─ dedup (place_id, phone)     │
                    │  seed_new_leads / daily_queue (throttle)    │
                    │  draft_messages (personalized, consent-first)│
                    │  update_status: new→queued→sent→replied→won  │
                    └─────────────────────────────────────────────┘
                                   │  (outbound scripts historically here —
                                   │   removed from repo, documented only)
                    postgres (n8n results, gmaps_leads)
```

---

## 3. Dependency Map

| Component | Depends on | Notes |
|---|---|---|
| main_api.py | scraper.py, extractor.py, FastAPI/uvicorn | 2 endpoints, sync scrape via asyncio |
| scraper.py | Playwright, browser binaries | headless flags, random delays |
| extractor.py | regex/stdlib only | stable patterns prioritized; obfuscated classes LAST |
| pipeline/*.py | sqlite3 stdlib, CSV | no external ORM |
| Dockerfile | python:3.10-slim + Playwright deps | pinned image version |
| docker-compose | postgres:15-alpine, n8n:latest | network `shark` |
| n8n json.json | scraper-api service name, postgres creds | DB: gmaps_leads |

Runtime model: **playwright + fastapi + sqlite + optional postgres/n8n**. No ML deps, no auth deps, no email libs yet.

---

## 4. Feature Inventory (v2 capabilities)

**Works (verified by code):**
- Async Google Maps scraping by query (name, place_id, coords, address, rating, reviews_count, categories, website, phone, thumbnail, hours)
- Stability-prioritized DOM extraction w/ fallbacks
- Sleep/delay + headless control for rate etiquette
- CSV/JSON results export
- SQLite CRM: lead import (deduped by place_id + phone), seeding, daily queue throttling, drafted personalized intro messages, status state machine
- n8n orchestration example
- Docker + docker-compose deployment

**Missing / removed (must be rebuilt for v3):**
- Any service catalog / offer definition
- Portfolio evidence registry / matching engine / scoring
- Email (IMAP inbound, Nodemailer outbound)
- Dashboards / reporting
- Auth & role separation
- Tests (none present)
- Migration tooling (no Alembic or equivalent)

---

## 5. Gap Assessment vs CLIENTFINDER v3 Spec

| Spec area | v2 status | v3 work needed |
|---|---|---|
| Scraping + enrichment pipeline | present | keep; harden (redis queue, resume, dedupe). |
| Service catalog (verified) | absent | NEW module `service_catalog` |
| Portfolio evidence registry | absent | NEW module `portfolio` |
| Matching engine | absent | NEW `matching` (regex+keyword+LLM-capable) |
| Scoring & prioritization | partial (daily_queue) | NEW `scoring` (fit score) |
| Reason/conflict tracking | absent | audits table |
| Email inbound (IMAP) | absent | NEW `email` service |
| Email outbound (Nodemailer) | absent | NEW `email` service |
| Dashboards | absent | NEW `dashboard` (FastAPI + static) |
| Auth/RBAC | absent | NEW `auth` (env-secret, roles) |
| Tests | absent | pytest suite |
| Docker | exists | extend compose (email, worker, db) |
| Lang selection | Python | keep Python/FastAPI (matches stack) |

---

## 6. v3 Architecture (proposal)

```
                         ┌───────────────────────────────────────────┐
                         │           CLIENTFINDER v3 API (:8001)     │
                         │   FastAPI (existing) + new routers         │
                         └───────────────────────────────────────────┘
     routers:  /catalog  /portfolio  /matching  /scoring  /leads
               /email:inbox /email:drafts  /auth  /dashboard
                         │
        ┌────────────────┼───────────────────────────────┐
        ▼                ▼                               ▼
  service_catalog   portfolio (evidence)             leads (v2 pipeline)
  ─────────────      ──────────────────               ─────────────────
  services table    portfolio_evidence table          leads / interactions (existing)
  verified tiers   (project evidence, URLs)           + new: lead_scores,
  filled_answers                                        lead_matches,
                                                        audits
        └─────────────────┬───────────────────────┘
                          ▼
                 matching / scoring engine
                          ▼
                 email subsystem
                  - IMAP inbound service (new)
                  - Nodemailer outbound (new)
                  - drafts only (human-in-loop)
                          ▼
                 Dashboard (read-only views + audit)
```

Storage: **SQLite as source of truth** (existing `crm.db` preserved via migration), optional Postgres for n8n results stays separate. Migration runner in `pipeline/migrate.py` (no external ORM, honest to stack).

---

## 7. DB Migration Plan (preserving crm.db data)

Approach: additive migrations, never destructive, idempotent, run in a transaction per file.

1. Baseline: own `pipeline/init_db.py` schema (`leads`, `interactions`, `fields` as defined). Migration v0 = no-op reflection of existing tables.
2. `v1_service_catalog.sql`: `services`, `service_tiers`, `filled_answers`, `service_evidence_link`.
3. `v2_portfolio.sql`: `portfolio_evidence` (project_name, role, description, skills[], url, evidence_type, provenance, verified_on, confidence).
4. `v3_matching.sql`: `lead_matches` (lead_id, service_id, score, matched_on[], explanation, status).
5. `v4_scoring.sql`: `lead_scores` (lead_id, fit_score, components JSON, updated_at).
6. `v5_audit.sql`: `audit_log` (ts, actor, action, entity, before/after JSON, reason) + trigger hooks.
7. `v6_email.sql`: `email_accounts`, `email_messages` (uid, mailbox, subject, body, from/to, replied), `email_drafts`.
8. `v7_auth.sql`: `users`, `sessions`/api keys, roles.

Rules: KEEP `leads` untouched structurally; only add FK columns when necessary; back up `crm.db` before first migration (copy to `pipeline/crm.db.bak-<date>`); record applied versions in `schema_migrations`.

---

## 8. Implementation Sequence (phased, matching spec)

1. **Phase 1 — Service catalog**: `service_catalog` DB + models + seed real services (verified →8 tiers→familiarity→unvalidated), filled-answer prompt pack, API CRUD, tests.
2. **Phase 2 — Portfolio evidence registry**: `portfolio` DB + ingestion API + provenance (MY_PROJECTS.md-equivalent), tests.
3. **Phase 3 — Matching engine**: keyword/regex service-matching over leads+scrape data w/ scored reasons, API, tests.
4. **Phase 4 — Scoring**: fit-score components (need * fit * urgency * size), thresholds, lead_scores, API, tests.
5. **Phase 5 — Reason/conflict detection & audits**: rule engine + audit persistence.
6. **Phase 6 — Lead queue upgrade**: worker, resumable queue (replaces daily_queue throttling internals), backoff.
7. **Phase 7 — Reports**: static report generation (CSV/JSON/markdown) per lead + match summary.
8. **Phase 8 — Email inbound**: IMAP service (read-only, UID-based, store into email_messages; never auto-send).
9. **Phase 9 — Email outbound**: Nodemailer drafts + send-box with explicit gate; dry-run default.
10. **Phase 10 — Email automation**: reply-matching + suggested draft personalization.
11. **Phase 11 — Dashboards**: HTML/JS static dashboard served by FastAPI + JSON endpoints.
12. **Phase 12 — Auth/RBAC**: secret-key token auth, role admin|operator|viewer.
13. **Phase 13 — Config & secrets**: pydantic-settings/.env schema (note: NOT email IMAP passwords in reverse).
14. **Phase 14 — Persistence upgrades**: retention, archiving, exports.
15. **Phase 15 — Operations**: runs via cron, logging to file, error alerting (mailto), Docker compose additions.
16. **Phase 16 — Full test + hardening**: pytest suite, security review, reconnect-safe scraping.
17. **Phase 17 — Deploy + docs**: docs/CLIENTFINDER_V3_WHITEPAPER.md, compose for email/worker/db, install script.

Human-in-the-loop: every outbound message is a DRAFT unless an admin flips a per-account "send enabled" gate.

---

## 9. Reusable Components (from v2)

- `scraper.py` — asyncio/Playwright scraper (keep, extend resume)
- `extractor.py` — DOM extraction (keep as-is)
- `main_api.py` — FastAPI app skeleton, logger, run_scrape runners (extend w/ routers)
- `pipeline/init_db.py` — sqlite bootstrap pattern (extend with `migrate.py`)
- `pipeline/daily_queue.py` — throttling concept (fold into Phase 6 worker)
- `docs/PIPELINE_BRIEF.md` — the authoritative v2 pipeline doc to preserve
- `Dockerfile`/`docker-compose.yml` — deployment baseline

New modules (additive, no v2 modifications until integration points): `service_catalog/`, `portfolio/`, `matching/`, `scoring/`, `email/`, `dashboard/`, `audit/`, `auth/`.

---

## 10. Risk Register

| # | Risk | Mitigation |
|---|---|---|
| R1 | ~~No real Python on this machine (MS-store stub hangs)~~ **RESOLVED** | real Python 3.12 installed via `winget` (user-scope, no admin); tests now run locally. Docker remains optional |
| R2 | v2 outreach/DM scripts deleted from repo; only docs remain | reconstruct behavior from `docs/PIPELINE_BRIEF.md`; keep v3 email draft-only |
| R3 | Google Maps scraping ToS / blocking | preserve rate limits, random delays, consent-first, fail-safe halt (AGENTS.md) |
| R4 | Data-reach: no live scraped leads available for matching tests | use fixture CSVs; tests use synthetic-but-realistic fixture data |
| R5 | Personalization evidence (resume/projects) must be real | service catalog marked **verified/project/familiarity/unvalidated** by provenance; user must review contents |
| R6 | Anti-spam flag | strict per-account throttling, uniqueness (AGENTS.md), draft-only default |
| R7 | Schema drift between sqlite (pipelines) and postgres (n8n) | add migrations, doc data flow, single source of truth = sqlite |
| R8 | Long build | do phases in dependency order; deliver + review at 3-4 milestones |

---

## 11. Open Questions Before Phase 1

1. Confirm this repo copy at `C:\Users\hsing\clientfinder-v3` is the working tree for v3 (I will NOT commit/push without a green light).
2. Personalization: I need the **real, currently-verified** list of services + evidence (name, role, link) for the catalog seed — the spec allows empty-but-structured start. Do you want me to seed from `docs/PIPELINE_BRIEF.md`/README only, or do you provide your own service list?
3. Email test accounts: provide IMAP server/port and a test sender for Phase 8–10, or is config-only fine for now (no real credentials in repo)?
4. Docker vs local Python for running tests later? (No real python on this box.)

Next step pending your go-ahead: Phase 1 (service catalog) implementation.