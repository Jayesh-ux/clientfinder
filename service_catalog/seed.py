"""Seed catalog for CLIENTFINDER v3.

Idempotent + refreshing: seeded rows are created if absent and refreshed in
place if present (keyed by unique slug), so catalog evolution propagates.
Rows that were created through the API (unknown slugs) are never touched.
Provenance policy: nothing is marked 'verified' automatically; any evidence
comes from the documented project/resume material and is reported as such.
Only the current repository (google-map-scraper / CLIENTFINDER) is marked
verified because it exists in this working tree.
"""

import json
import os

from .db import connect
from .repository import (
    create_capability, create_evidence, create_solution, create_problem_pattern,
    get_capability_by_slug, get_solution_by_slug, update_problem_pattern,
)

evidence_ids = {}

EVIDENCE_SEED = [
    {
        "project_name": "FairPay",
        "role": "Builder",
        "description": "Pay equity tooling; builds structured pay bands and transparency "
                       "to remove bias from compensation decisions.",
        "skills_used": ["python", "fastapi", "sql", "llm"],
        "url": None, "date_label": None, "outcome": None,
        "provenance": "reported", "verified": False,
    },
    {
        "project_name": "Hire2Onboard",
        "role": "Builder",
        "description": "Hiring-to-onboarding workflow automation for HR teams; reduces "
                       "manual coordination across candidate, offer, and onboarding stages.",
        "skills_used": ["python", "fastapi", "react", "node", "sql"],
        "url": None, "date_label": None, "outcome": None,
        "provenance": "reported", "verified": False,
    },
    {
        "project_name": "career grid",
        "role": "Builder",
        "description": "Job-application tracking product; structured pipeline views, "
                       "filters, and reminders for job seekers.",
        "skills_used": ["react", "node", "sql"],
        "url": None, "date_label": None, "outcome": None,
        "provenance": "reported", "verified": False,
    },
    {
        "project_name": "GeoTrack",
        "role": "Builder",
        "description": "Geofenced time tracking for staff at remote sites; verifies "
                       "real-time presence and generates attendance without manual "
                       "check-ins.",
        "skills_used": ["react-native", "websockets", "geofencing", "node", "sql"],
        "url": None, "date_label": None, "outcome": None,
        "provenance": "reported", "verified": False,
    },
    {
        "project_name": "google-map-scraper (CLIENTFINDER base)",
        "role": "Maintainer",
        "description": "Google Maps lead scraper + SQLite CRM pipeline (FastAPI + "
                       "Playwright). Present in this working tree; usable as a verified "
                       "component for lead-generation automation.",
        "skills_used": ["python", "fastapi", "playwright", "webscraping", "sql"],
        "url": None, "date_label": "2026", "outcome": None,
        "provenance": "repo_local", "verified": True,
    },
]

CAPABILITY_SEED = [
    {"slug": "python", "name": "Python", "category": "Backend",
     "description": "General Python development.", "proficiency": "advanced",
     "verification_level": "verified_project", "evidence": "FairPay"},
    {"slug": "fastapi", "name": "FastAPI / REST APIs", "category": "Backend",
     "description": "API design, background tasks, async FastAPI services.",
     "proficiency": "advanced", "verification_level": "verified_project",
     "evidence": "FairPay"},
    {"slug": "react", "name": "React", "category": "Frontend",
     "description": "SPA development with modern React.", "proficiency": "advanced",
     "verification_level": "familiarity", "evidence": None},
    {"slug": "node", "name": "Node.js", "category": "Backend",
     "description": "Server-side JavaScript / automation workflows.",
     "proficiency": "intermediate", "verification_level": "familiarity", "evidence": None},
    {"slug": "react-native", "name": "React Native / Mobile", "category": "Mobile",
     "description": "Cross-platform mobile applications.", "proficiency": "advanced",
     "verification_level": "familiarity", "evidence": "GeoTrack"},
    {"slug": "websockets", "name": "WebSockets / Realtime", "category": "Backend",
     "description": "Low-latency realtime data delivery.", "proficiency": "intermediate",
     "verification_level": "familiarity", "evidence": "GeoTrack"},
    {"slug": "geofencing", "name": "Geofencing / Location", "category": "Mobile",
     "description": "Location-aware features, geofenced triggers, presence verification.",
     "proficiency": "intermediate", "verification_level": "familiarity",
     "evidence": "GeoTrack"},
    {"slug": "playwright", "name": "Playwright / Browser Automation", "category": "Automation",
     "description": "Headless browser scraping and automation (see repository).",
     "proficiency": "advanced", "verification_level": "verified_project",
     "evidence": "google-map-scraper (CLIENTFINDER base)"},
    {"slug": "webscraping", "name": "Web Scraping / Data Extraction", "category": "Automation",
     "description": "Stability-prioritized DOM extraction, large-scale lead discovery.",
     "proficiency": "advanced", "verification_level": "verified_project",
     "evidence": "google-map-scraper (CLIENTFINDER base)"},
    {"slug": "sql", "name": "SQL / Relational DBs", "category": "Data",
     "description": "Schema design, queries, migrations; SQLite/PostgreSQL.",
     "proficiency": "advanced", "verification_level": "verified_project",
     "evidence": "google-map-scraper (CLIENTFINDER base)"},
    {"slug": "llm", "name": "LLM APIs / AI Integration", "category": "AI",
     "description": "LLM-powered features: generation, classification, extraction.",
     "proficiency": "intermediate", "verification_level": "familiarity", "evidence": None},
    {"slug": "hiring", "name": "Hiring / Talent Workflows", "category": "Domain",
     "description": "Recruiting, pay equity, onboarding, applicant tracking.",
     "proficiency": "advanced", "verification_level": "verified_project",
     "evidence": "Hire2Onboard"},
    {"slug": "consulting", "name": "Technical Consulting / Discovery", "category": "Domain",
     "description": "Translating business problems into buildable solutions; scoping, "
                    "tradeoffs, incremental delivery.", "proficiency": "advanced",
     "verification_level": "familiarity", "evidence": None},
]

SOLUTION_SEED = [
    {
        "slug": "lead-gen-automation",
        "name": "Lead-Generation & Sales Automation",
        "summary": "Discover, enrich, and prioritize new customers automatically from "
                   "public data (e.g., Google Maps), into a CRM pipeline with outreach.",
        "problem_text": "Businesses relying on word of mouth cannot systematically find "
                        "new customers.",
        "deliverables": ["Automated lead discovery", "CRM / pipeline with dedupe",
                         "Personalised outreach drafts", "Follow-up queue"],
        "capability_slugs": ["playwright", "webscraping", "python", "fastapi", "sql", "llm"],
        "evidence_names": ["google-map-scraper (CLIENTFINDER base)"],
        "typical_effort_label": "2-6 weeks", "is_active": True,
    },
    {
        "slug": "custom-web-application",
        "name": "Custom Web Application",
        "summary": "Tailor-made internal or customer-facing web apps, from database design "
                   "to polished UI.",
        "problem_text": "Off-the-shelf software does not match the business's actual "
                        "process.",
        "deliverables": ["Web app (React / FastAPI)", "Database schema", "Auth & roles",
                         "Deployment"],
        "capability_slugs": ["python", "fastapi", "react", "node", "sql"],
        "evidence_names": ["FairPay", "Hire2Onboard", "career grid"],
        "typical_effort_label": "3-12 weeks", "is_active": True,
    },
    {
        "slug": "realtime-tracking-dashboard",
        "name": "Realtime Location / Attendance Dashboard",
        "summary": "Geofenced presence verification and live dashboards for staff or "
                   "assets at remote sites.",
        "problem_text": "No visibility into where people/assets are and who actually "
                        "showed up.",
        "deliverables": ["Geofenced check-in", "Realtime dashboard (WebSockets)",
                         "Attendance reports", "Mobile app"],
        "capability_slugs": ["react-native", "websockets", "geofencing", "node", "sql"],
        "evidence_names": ["GeoTrack"],
        "typical_effort_label": "4-8 weeks", "is_active": True,
    },
    {
        "slug": "hiring-onboarding-platform",
        "name": "Hiring / Onboarding Platform",
        "summary": "Structured pipelines for candidates, offers, and onboarding; pay "
                   "band tooling for fairness.",
        "problem_text": "Hiring and onboarding run on spreadsheets and email threads; "
                        "decisions lack structure.",
        "deliverables": ["Applicant pipeline", "Offer / onboarding workflow",
                         "Pay band & equity tooling", "Deployment"],
        "capability_slugs": ["hiring", "python", "fastapi", "react", "sql", "llm"],
        "evidence_names": ["FairPay", "Hire2Onboard", "career grid"],
        "typical_effort_label": "3-10 weeks", "is_active": True,
    },
    {
        "slug": "digital-presence-booking",
        "name": "Website, Local SEO & Online Booking",
        "summary": "A modern mobile-first website, local search visibility, and an "
                   "online booking funnel so customers can find the business and "
                   "book without phone tags.",
        "problem_text": "Customers cannot reliably find the business online, and "
                        "scheduling depends on phone calls.",
        "deliverables": ["Mobile-first website", "Local SEO (Google Business + maps)",
                         "Online booking / enquiry funnel", "WhatsApp scheduling links",
                         "Basic analytics"],
        "capability_slugs": ["react", "fastapi", "python", "webscraping", "sql",
                             "consulting"],
        "evidence_names": ["FairPay", "Hire2Onboard", "google-map-scraper (CLIENTFINDER base)"],
        "typical_effort_label": "2-5 weeks", "is_active": True,
    },
    {
        "slug": "ai-powered-tools",
        "name": "AI-Powered Internal Tools",
        "summary": "LLM-backed assistants for drafting, classification, extraction, and "
                   "report summarisation inside existing workflows.",
        "problem_text": "Staff spend hours on repetitive drafting/reading that an LLM "
                        "can do fast with human review.",
        "deliverables": ["LLM integration", "Prompt/config library", "Human-review UI",
                         "Guardrails & logging"],
        "capability_slugs": ["llm", "python", "fastapi", "react", "sql"],
        "evidence_names": [],
        "typical_effort_label": "2-6 weeks", "is_active": True,
    },
    {
        "slug": "inventory-stock-automation",
        "name": "Inventory & Stock Automation",
        "summary": "Track stock across locations in real time with reorder alerts, "
                   "so nothing is ever out of stock or sitting dead on shelves.",
        "problem_text": "Stock is counted on paper or in spreadsheets; shortages and "
                        "overstock both happen.",
        "deliverables": ["Live stock tracking", "Reorder / low-stock alerts",
                         "Supplier + pricing records", "Reporting"],
        "capability_slugs": ["python", "fastapi", "react", "node", "sql"],
        "evidence_names": ["FairPay", "career grid"],
        "typical_effort_label": "3-8 weeks", "is_active": True,
    },
    {
        "slug": "billing-payments-automation",
        "name": "Billing / Invoice / Payment Automation",
        "summary": "Generate invoices and receipts, chase pending payments, and keep "
                   "records tax-ready without manual math.",
        "problem_text": "Invoices and receipts are made by hand and money is not "
                        "reconciled against what was billed.",
        "deliverables": ["Invoice generation", "Receipt + payment tracking",
                         "Pending-dues follow-up", "Tax-ready records"],
        "capability_slugs": ["python", "fastapi", "react", "sql"],
        "evidence_names": ["FairPay"],
        "typical_effort_label": "2-6 weeks", "is_active": True,
    },
    {
        "slug": "retention-referral-loyalty",
        "name": "Retention, Referral & Loyalty Programs",
        "summary": "Reward repeat customers, spot who is about to churn, and turn "
                   "happy customers into a referral engine.",
        "problem_text": "Customer loyalty is informal; repeat visits and referrals are "
                        "not rewarded or measured.",
        "deliverables": ["Loyalty / points program", "Visit & spend tracking",
                         "Referral links", "Churn warnings"],
        "capability_slugs": ["react", "fastapi", "node", "sql"],
        "evidence_names": ["career grid"],
        "typical_effort_label": "2-6 weeks", "is_active": True,
    },
    {
        "slug": "multi-location-ops",
        "name": "Multi-Location Operations Hub",
        "summary": "One dashboard across branches/outlets: inventory, staffing, sales, "
                   "and alerts per location.",
        "problem_text": "Each branch runs independently; management has no single view "
                        "and decisions are guesses.",
        "deliverables": ["Branch hierarchy", "Per-location dashboards", "Cross-location "
                         "stock/roster sync", "Central alerts"],
        "capability_slugs": ["react", "fastapi", "react-native", "node", "sql",
                             "websockets"],
        "evidence_names": ["GeoTrack", "career grid"],
        "typical_effort_label": "4-10 weeks", "is_active": True,
    },
    {
        "slug": "scheduling-rosters",
        "name": "Staff Scheduling & Rosters",
        "summary": "Shift plans, leave requests, and roster swaps on a calendar every "
                   "employee can open.",
        "problem_text": "Shift rosters are managed in group chats; swaps, leaves, and "
                        "who-is-when are constantly re-negotiated.",
        "deliverables": ["Shift calendar", "Leave / swap requests", "Coverage alerts",
                         "Payroll-ready hours export"],
        "capability_slugs": ["python", "fastapi", "react", "sql"],
        "evidence_names": ["Hire2Onboard"],
        "typical_effort_label": "3-6 weeks", "is_active": True,
    },
    {
        "slug": "document-management",
        "name": "Document Management & Search",
        "summary": "A searchable, permission-controlled home for contracts, records, "
                   "and files — no more digging through folders and chat history.",
        "problem_text": "Important records live in papers, folders, and chat; finding "
                        "one document costs hours.",
        "deliverables": ["Upload + OCR/indexing", "Full-text search", "Permission levels",
                         "Audit trail"],
        "capability_slugs": ["python", "fastapi", "react", "sql", "llm"],
        "evidence_names": [],
        "typical_effort_label": "3-8 weeks", "is_active": True,
    },
    {
        "slug": "customer-comms-automation",
        "name": "Customer Communication Automation",
        "summary": "Routine updates — reminders, order status, follow-ups — go out "
                   "automatically via WhatsApp/email without manual typing.",
        "problem_text": "Staff manually send the same reminders and updates to every "
                        "customer, one by one.",
        "deliverables": ["Reminder / follow-up flows", "WhatsApp/email delivery",
                         "Send-rate limits & opt-outs", "Response tracking"],
        "capability_slugs": ["python", "fastapi", "react", "node", "llm", "playwright"],
        "evidence_names": ["google-map-scraper (CLIENTFINDER base)"],
        "typical_effort_label": "2-6 weeks", "is_active": True,
    },
    {
        "slug": "reports-dashboards",
        "name": "Reports & Live Dashboards",
        "summary": "Pull scattered numbers into one dashboard with the KPIs the owner "
                   "actually checks, refreshed automatically.",
        "problem_text": "Numbers live across different systems and nobody gets a "
                        "clean weekly picture.",
        "deliverables": ["KPI dashboard", "Automated data pulls", "Email/WhatsApp "
                         "digests", "Exportable reports"],
        "capability_slugs": ["python", "fastapi", "react", "sql", "websockets"],
        "evidence_names": ["GeoTrack", "career grid"],
        "typical_effort_label": "2-5 weeks", "is_active": True,
    },
    {
        "slug": "field-service-jobs",
        "name": "Field Service Job Management",
        "summary": "Assign, track, and close jobs for technicians in the field with "
                   "real-time status.",
        "problem_text": "Field jobs are assigned over the phone and completion is "
                        "tracked by memory.",
        "deliverables": ["Job assignment", "Status tracking", "Technician mobile app",
                         "Customer updates"],
        "capability_slugs": ["react-native", "websockets", "geofencing", "node", "sql"],
        "evidence_names": ["GeoTrack"],
        "typical_effort_label": "4-8 weeks", "is_active": True,
    },
]

PATTERN_SEED = [
    {"slug": "finding-customers",
     "label": "Need more customers / leads",
     "keywords": [
         "need more customer", "find new customer", "new client", "more leads",
         "no pipeline", "rely on referrals", "dependent on word of mouth",
         "no enquiry", "not enough business", "grow sales", "boost revenue",
         "inbound enquiry", "no marketing", "how to get customers",
     ],
     "description": "Business depends on referrals/inbound and cannot systematically "
                    "find new prospects.",
     "solution_slug": "lead-gen-automation", "is_active": True},
    {"slug": "manual-repetitive-work",
     "label": "Manual repetitive work",
     "keywords": [
         "manual data entry", "copy data", "re-enter data", "retype", "double entry",
         "paperwork burden", "form processing", "hours on admin", "repetitive task",
         "filing manually", "data from pdf", "extract from email",
     ],
     "description": "Staff manually copy data between systems or redo the same task.",
     "solution_slug": "ai-powered-tools", "is_active": True},
    {"slug": "staff-tracking",
     "label": "Track staff / attendance",
     "keywords": [
         "attendance problem", "time tracking", "who is on site", "remote sites",
         "field staff whereabouts", "manual check in", "no attendance record",
         "staff showing up", "track employees location",
     ],
     "description": "No reliable record of staff presence or activity, especially at "
                    "remote sites.",
     "solution_slug": "realtime-tracking-dashboard", "is_active": True},
    {"slug": "hiring-chaos",
     "label": "Hiring / onboarding chaos",
     "keywords": [
         "candidate pipeline", "job applications scattered", "onboarding paperwork",
         "offer management", "recruitment tracking", "applicant tracking",
         "screening manually", "hiring process messy",
     ],
     "description": "Candidate and onboarding data scattered across tools; no structured "
                    "pipeline.",
     "solution_slug": "hiring-onboarding-platform", "is_active": True},
    {"slug": "no-custom-tool",
     "label": "Generic software doesn't fit",
     "keywords": [
         "software doesn't fit", "need custom tool", "bespoke system",
         "off the shelf doesn't work", "unique workflow", "generic app no",
         "can't adapt the tool", "our process is different",
     ],
     "description": "Off-the-shelf tools force the business to change its process.",
     "solution_slug": "custom-web-application", "is_active": True},
    {"slug": "no-online-presence",
     "label": "No or weak online presence",
     "keywords": [
         "no website", "no online presence", "no online booking",
         "not mobile responsive", "outdated website", "cannot book online",
         "calls for every booking", "no online catalogue", "no google listing",
         "customers cannot find us online", "manual booking by phone",
     ],
     "description": "Customers cannot find or book the business online; scheduling "
                    "depends on phone calls and referrals.",
     "solution_slug": "digital-presence-booking", "is_active": True},
    {"slug": "stock-issues",
     "label": "Stock / inventory issues",
     "keywords": [
         "stock outs", "overstock", "dead stock", "manual stock count",
         "inventory errors", "reorder manually", "no reorder alerts",
         "don't know what's in stock", "stock mismatches", "inventory tracking",
     ],
     "description": "Stock is counted by hand or in spreadsheets; shortages and "
                    "overstock both happen.",
     "solution_slug": "inventory-stock-automation", "is_active": True},
    {"slug": "billing-receipts",
     "label": "Billing / invoice issues",
     "keywords": [
         "manual invoices", "recurring invoices", "chasing payments",
         "pending dues", "payment tracking", "receipts by hand",
         "gst compliance", "reconcile billing", "no billing system",
     ],
     "description": "Invoices and receipts are made by hand and money is not "
                    "reconciled against what was billed.",
     "solution_slug": "billing-payments-automation", "is_active": True},
    {"slug": "retention-referrals",
     "label": "Retention / referrals weak",
     "keywords": [
         "repeat customers", "customer churn", "no loyalty program",
         "referral program", "retention problem", "customers don't come back",
         "no rewards for regular", "win back customers",
     ],
     "description": "Customer loyalty is informal; repeat visits and referrals are not "
                    "rewarded or measured.",
     "solution_slug": "retention-referral-loyalty", "is_active": True},
    {"slug": "multi-location-blind",
     "label": "Multiple locations uncoordinated",
     "keywords": [
         "multiple branches", "chain of stores", "each branch separate",
         "no central view", "per location reports", "franchise operations",
         "branch performance", "locations independently",
     ],
     "description": "Each branch runs independently; management has no single view and "
                    "decisions are guesses.",
     "solution_slug": "multi-location-ops", "is_active": True},
    {"slug": "roster-scheduling",
     "label": "Shift / roster scheduling pain",
     "keywords": [
         "shift rosters", "leave requests", "roster swaps", "who is working when",
         "shift plan", "schedule changes chaos", "staff timings",
         "coverage on leave", "marking attendance shift",
     ],
     "description": "Shift rosters are managed in group chats; swaps, leaves, and "
                    "who-is-when are constantly re-negotiated.",
     "solution_slug": "scheduling-rosters", "is_active": True},
    {"slug": "records-scattered",
     "label": "Records / documents scattered",
     "keywords": [
         "can't find documents", "records in folders", "files in chat",
         "documents scattered", "paper records", "searching paperwork",
         "central document store", "contracts everywhere", "record keeping manual",
     ],
     "description": "Important records live in papers, folders, and chat; finding one "
                    "document costs hours.",
     "solution_slug": "document-management", "is_active": True},
    {"slug": "customer-communication-manual",
     "label": "Customer updates are manual",
     "keywords": [
         "manual reminders", "appointment reminders", "order updates manually",
         "follow up with customers", "send same message", "whatsapp blast manual",
         "customer updates one by one", "no automatic reminders",
     ],
     "description": "Staff manually send the same reminders and updates to every "
                    "customer, one by one.",
     "solution_slug": "customer-comms-automation", "is_active": True},
    {"slug": "no-reports-insight",
     "label": "No reports / insight",
     "keywords": [
         "numbers scattered", "no dashboard", "weekly reports by hand",
         "can't see performance", "data in different systems",
         "manual reporting", "no visibility into numbers",
     ],
     "description": "Numbers live across different systems and nobody gets a clean "
                    "weekly picture.",
     "solution_slug": "reports-dashboards", "is_active": True},
    {"slug": "field-jobs",
     "label": "Field jobs unmanaged",
     "keywords": [
         "assign jobs by phone", "technician tracking", "service calls in the field",
         "job status unknown", "field visits", "onsite jobs", "completion by memory",
         "dispatch field team",
     ],
     "description": "Field jobs are assigned over the phone and completion is tracked "
                    "by memory.",
     "solution_slug": "field-service-jobs", "is_active": True},
]


def seed(override_db_path=None):
    """Idempotently seed the catalog.

    All repository operations open connections resolved from the standard
    DB-path rules. Pass override_db_path to seed an explicit database file
    (used by the migration CLI).
    """
    if override_db_path is not None:
        old = os.environ.get("CLIENTFINDER_DB_PATH")
        os.environ["CLIENTFINDER_DB_PATH"] = str(override_db_path)
        try:
            _seed_impl()
        finally:
            if old is None:
                os.environ.pop("CLIENTFINDER_DB_PATH", None)
            else:
                os.environ["CLIENTFINDER_DB_PATH"] = old
    else:
        _seed_impl()


def _seed_impl():
    conn = connect()
    try:
        for item in EVIDENCE_SEED:
            name = item["project_name"]
            existing = conn.execute(
                "SELECT id FROM portfolio_evidence WHERE project_name = ?",
                (name,)).fetchone()
            if existing:
                evidence_ids[name] = existing["id"]
            else:
                created = create_evidence(item)
                evidence_ids[name] = created["id"]

        for cap in CAPABILITY_SEED:
            if get_capability_by_slug(cap["slug"]):
                continue
            cap_data = dict(cap)
            cap_data.pop("evidence", None)
            cap_data["evidence_id"] = evidence_ids.get(cap.get("evidence"))
            create_capability(cap_data)

        for sol in SOLUTION_SEED:
            sol_data = dict(sol)
            sol_data.pop("evidence_names", None)
            sol_data["evidence_ids"] = [
                evidence_ids.get(n) for n in sol.get("evidence_names", [])
                if evidence_ids.get(n) is not None]
            if get_solution_by_slug(sol["slug"]):
                update_solution_by_slug(sol["slug"], sol_data)
            else:
                create_solution(sol_data)

        for pat in PATTERN_SEED:
            existing = conn.execute("SELECT id FROM problem_patterns WHERE slug = ?",
                                    (pat["slug"],)).fetchone()
            if existing:
                update_problem_pattern(existing["id"], {
                    "label": pat["label"],
                    "keywords": pat["keywords"],
                    "description": pat.get("description"),
                    "solution_slug": pat["solution_slug"],
                    "is_active": pat.get("is_active", True),
                })
            else:
                create_problem_pattern(pat)
    finally:
        conn.close()


def update_solution_by_slug(slug, sol_data):
    """Update a seeded solution in place by slug (keeps links in sync)."""
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id FROM solution_templates WHERE slug = ?", (slug,)).fetchone()
        if row is None:
            return None
        sol_id = row["id"]
        fields = {
            "name": sol_data["name"],
            "summary": sol_data.get("summary"),
            "problem_text": sol_data.get("problem_text"),
            "deliverables": sol_data.get("deliverables"),
            "typical_effort_label": sol_data.get("typical_effort_label"),
            "is_active": sol_data.get("is_active", True),
            "capability_slugs": sol_data.get("capability_slugs", []),
            "evidence_ids": sol_data.get("evidence_ids", []),
        }
        conn.execute(
            "UPDATE solution_templates SET name = ?, summary = ?, problem_text = ?,"
            " deliverables = ?, typical_effort_label = ?, is_active = ?,"
            " updated_at = datetime('now') WHERE id = ?",
            (fields["name"], fields["summary"], fields["problem_text"],
             json.dumps(fields["deliverables"] or []),
             fields["typical_effort_label"], 1 if fields["is_active"] else 0,
             sol_id))
        _set_solution_links(conn, sol_id, fields["capability_slugs"], fields["evidence_ids"])
        conn.commit()
        return sol_id
    finally:
        conn.close()


def _set_solution_links(conn, sol_id, capability_slugs, evidence_ids):
    conn.execute("DELETE FROM solution_capabilities WHERE solution_id = ?", (sol_id,))
    for slug in capability_slugs:
        row = conn.execute("SELECT id FROM capabilities WHERE slug = ?", (slug,)).fetchone()
        if row:
            conn.execute(
                "INSERT OR IGNORE INTO solution_capabilities (solution_id, capability_id)"
                " VALUES (?, ?)", (sol_id, row["id"]))
    conn.execute("DELETE FROM solution_evidence WHERE solution_id = ?", (sol_id,))
    for ev_id in evidence_ids:
        conn.execute(
            "INSERT OR IGNORE INTO solution_evidence (solution_id, evidence_id)"
            " VALUES (?, ?)", (sol_id, ev_id))


if __name__ == "__main__":
    seed()
    print("Catalog seed complete.")