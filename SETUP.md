# ClientFinder v3 — Setup Guide

End-to-end local business lead generation + email outreach for Mumbai area.
Scrape business data → store leads in SQLite → match offers → generate
HTML-styled outreach/follow-up emails (drafts) → operator approves → send via Gmail.

> **Human-in-the-loop by design.** Nothing ever sends automatically. Every email
> is created as a `draft`, and sending requires your explicit approval +
> `send_enabled=1` on the mailbox.

---

## 1. Prerequisites

- Python **3.10+** (tested on 3.12 Windows, 3.13 Linux/Termux arm64)
- A Gmail account with an **App Password** (for SMTP + IMAP).
  Enable 2FA → Google Account → Security → App passwords → generate one.
- Node.js **18+** (only for the n8n/compose side; the scraper itself is Python).

---

## 2. Clone & install

```bash
git clone https://github.com/Jayesh-ux/clientfinder.git
cd clientfinder

python -m venv .venv
# Windows:
.venv\Scripts\activate
# mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt
playwright install chromium
```

Already have a Chromium build on the machine? Skip the 190 MB download and point
Playwright at it instead (revision mismatches are the usual reason `playwright
install` is skipped):

```bash
echo 'CF_BROWSER_EXECUTABLE=/path/to/chrome' >> .env
```

Run the test suite to confirm the machine is ready:

```bash
python -m pytest -q
```

---

## 3. Secrets (`.env`)

Copy `.env.example` to `.env` at the repo root. `.env` is git-ignored — never
commit it.

```
CF_SMTP_PASSWORD=your_gmail_app_password
CF_IMAP_PASSWORD=your_gmail_app_password
CF_BROWSER_EXECUTABLE=/optional/path/to/chrome
```

`.env` is loaded automatically by `service_catalog/config.py`, so every script
and the API see the same values. The DB path defaults to `pipeline/crm.db`;
override with `CLIENTFINDER_DB_PATH`. The same Gmail app password works for
SMTP (send) and IMAP (inbound).

Working directories (git-ignored, auto-created):

| Path               | Holds                                                        |
|--------------------|--------------------------------------------------------------|
| `data/raw/`        | scrape JSON, import CSVs, harvest progress                  |
| `data/outreach/`   | `lead_dossiers.md`, `all_leads_export.csv`, call lists       |

---

## 4. First run — create the schema + mailbox

```bash
python pipeline/init_db.py        # creates the leads table if missing
python pipeline/migrate.py --seed # applies migrations + seeds the catalog
```

Register the mailbox the draft generators send from (the generators look it up
by `from_email`, so this must exist before step 7):

```bash
python pipeline/setup_mailbox.py --email you@gmail.com --name "Your Name"
python pipeline/setup_mailbox.py --list
```

Use `--disable-send` to register it with `send_enabled=0` (drafts only, nothing
can send). Flip it later with
`python pipeline/setup_mailbox.py --email you@gmail.com`.

Optionally seed the demo clinic leads:

```bash
python pipeline/seed_new_leads.py
```

> The draft generators pick their account by `from_email`, so register the
> mailbox you want them to use (default in the scripts:
> `hsinghjayesh@gmail.com`).

---

## 5. Find leads

### 5a. Scrape Google Maps (optional)
Queries live in `pipeline/queries_*.txt` (one query per line).

```bash
python pipeline/run_scrape.py "dentist in Kalyan" --max 20
python pipeline/run_scrape.py --queries-file pipeline/queries_mumbai.txt --max 10
```

Output lands in `data/raw/leads_scraped.json` (override with `--out`). Import it:

```bash
python pipeline/scrape_to_leads.py leads_scraped.json
```

Alternatively import a raw CSV with `pipeline/import_leads.py`, or call the
API server instead of the CLI:

```bash
uvicorn gmaps_scraper_server.main_api:app --host 127.0.0.1 --port 8001
curl "http://127.0.0.1:8001/scrape-get?query=dentist%20in%20Kalyan&max_places=20"
```

### 5b. Harvest emails (optional, fills gaps)
```bash
python pipeline/harvest_emails.py             # 160 leads/round, resumes via data/raw/harvest_progress.json
```

---

## 6. Match & frame leads

```bash
python pipeline/match_leads.py                # scores each lead against solutions -> lead_matches / lead_scores
python pipeline/infer_problems.py --all       # observations + lead_problem / why_they_pay_us columns
python pipeline/update_problem_columns.py     # data/outreach/all_leads_export.csv
python pipeline/lead_dossiers.py              # data/outreach/lead_dossiers.md
```

---

## 7. Generate outreach DRAFTS (nothing sends)

```bash
python pipeline/make_outreach_drafts.py       # intro email (touch 1) for every emailed lead w/o a draft
python pipeline/make_followup_drafts.py       # follow-up drafts for leads already sent to
```

- Every draft gets a plain-text body **and** an injected HTML body
  (`pipeline/html_email_builder.py` + `templates/outreach-email.html`).
- Body + subject are chosen at random from high-entropy variant sets
  (anti-fingerprint). Subject/business names are per-lead.
- Multi-branch businesses sharing one inbox (e.g. a franchise chain with one
  central contact address) are deduplicated — only the first gets a draft; later
  ones are cancelled.

Inspect what you're about to send:

```bash
python -c "import sqlite3;c=sqlite3.connect('pipeline/crm.db');c.row_factory=sqlite3.Row;print([dict(r) for r in c.execute(\"select id,status,subject,lead_id from email_drafts where status in ('draft','approved') order by id\")][:20])"
```

---

## 8. Approve & send (explicit operator action)

Drafts start `status='draft'`. Sending = `approve_draft(id)` then `send_draft(id)`.
The account must have `send_enabled=1` and `CF_SMTP_PASSWORD` must be set.

Send a single draft:

```python
from service_catalog.email import approve_draft, send_draft  # loads .env for you
approve_draft(123)                 # the draft id
print(send_draft(123))
```

Batch-send (paced, from a temporary script — it reuses the same loop):
- iterate draft ids 255..310 style, `random.uniform(8, 20)`s between sends
- stop hard on auth/rate-limit errors (`"authentication"`, `"rate"`, `"temperror"`, ...)

> **Pacing rule:** the proven safe daily volume from one Gmail is ~56/day mixed
> (outreach + follow-ups). Do not blow past it — send in random-delay batches.

---

## 9. Receive replies (IMAP, read-only)

Replies are never auto-answered. Fetch + store them:

```python
import os
from service_catalog.email import fetch_inbox, list_accounts  # loads .env for you
for a in list_accounts():
    if a["send_enabled"]:
        print(a["id"], fetch_inbox(a["id"], os.environ["CF_IMAP_PASSWORD"]))
```

Inbound messages land in `email_messages` (Message-ID-deduplicated). Review them
and update lead `response_status` / `deal_stage` manually. `docs/outreach-flow.md`
covers the response playbook (first reply → qualify → 10-min call → proposal →
close; a real reply beats a warm lead).

---

## 10. Cadence (the sequence that wins)

| Touch | When        | What                                   | Script                         |
|-------|-------------|----------------------------------------|--------------------------------|
| 1     | Day 0       | Intro + free 2-day working sample      | `make_outreach_drafts.py`      |
| 2     | Day +3..4   | Replay, new angle + proof point        | `make_followup_drafts.py`      |
| 3     | Day +7      | Value-drop: 3 things found in their SEO| `make_followup_drafts.py`      |
| 4     | Day +14     | Time-boxed offer ("slotting you in")   | `make_followup_drafts.py`      |
| 5     | No reply    | Archive → phone/call list              | `lead_dossiers.py` → `phone_call_targets` (ignored) |

Cold-email expectations: even good campaigns convert ~1–3% per touch; most
answers arrive after 2–4 touches, and tracking the funnel (inbox replies + CRM
`response_status`) is mandatory before judging volume.

---

## 11. Common problems

- **Drafts have no HTML**: `create_draft` must receive `html_body` (fixed in
  `service_catalog/email.py`). If yours lacks it, run
  `python pipeline/backfill_html_bodies.py`.
- **`send_draft` says "draft must be approved"**: run `approve_draft(id)` first.
- **"account send not enabled"**: set `send_enabled=1` on the mailbox.
- **Reply never shows up**: run `fetch_inbox` (read-only, dedup by Message-ID).
- **Gmail rejects auth**: regenerate the App Password; it must match `.env`.
- **SMTP timeouts mid-batch**: transient — retry failed ids only (they stay
  `approved`); never resend already-`sent` rows.
- **`make_outreach_drafts.py` raises `StopIteration`**: no mailbox registered.
  Run `python pipeline/setup_mailbox.py --email you@gmail.com`.
- **Migration fails with `no such table: leads`**: run `pipeline/init_db.py`
  first — migrations build on the base schema it creates.
- **`no such column: lead_problem`**: DB predates migration 0005; run
  `python pipeline/migrate.py`.
- **Scraper exits with "Executable doesn't exist"**: the Playwright-managed
  Chromium revision is missing. Either `playwright install chromium` or set
  `CF_BROWSER_EXECUTABLE` in `.env` to a Chromium already on the machine.
- **Scrape returns `[]` with "Feed element not found"**: Google served a
  consent/anti-bot page. Retry, lower `--concurrency`, or raise `--delay`.

---

## 12. What is NOT committed (git-ignored)

`crm.db` and backups, `.env`, `.venv/`, `*.csv`, `pipeline/*_businesses.json`,
`pipeline/scrape_*.json`, `send_queue.json`, `queue_tracker.json`,
`harvest_progress.json`, everything under `data/raw/` and `data/outreach/`,
`lead_dossiers.md`, `phone_call_targets.md`, `*.out`, `*.err`.

Your live lead data stays local. To move a working DB to another machine, copy
`pipeline/crm.db` out-of-band (it is deliberately never pushed).