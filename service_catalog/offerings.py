"""CLIENTFINDER v3: sellable offerings — capability x need -> gig / SaaS.

This module is the "what can we actually sell" layer. It combines:
  - our capabilities (skills + evidence + verification tiers)
  - business need-types (symptom patterns, NOT niches)
  - the concrete deliverable (gig) and a productizable (SaaS) variant
  - outreach angle templates for human-reviewed drafting

Design rules:
  * Nothing here is bound to a business niche. An offering maps to a *symptom*
    (e.g. "no online booking") so any vertical that shows the symptom is a lead.
  * Coverage is the point: if a business shows a symptom we have an offering for
    it; if it doesn't, matching returns nothing (no forced sale).
  * Outreach is DRAFT-ONLY and personalized; the email layer refuses to send
    until an operator approves AND the account is send-enabled.
"""

OUTREACH_ANGLES = {
    "realtime-tracking-dashboard": {
        "angle": (
            "We build live GPS/activity dashboards of vehicles, people, or orders "
            "so operations can answer 'where is everything?' instantly."),
        "openers": [
            "{business} — if knowing where the van/team/order is requires a "
            "phone call, dispatch is a guess.",
            "Every 'where's the order?' call costs {business} minutes of someone's "
            "day, every day.",
            "Between jobs and movement, {business} runs on live-state questions "
            "that no one can actually answer live.",
        ],
        "hooks": [
            "A single live map of vehicles/people/orders with status history, "
            "alerts, and exportable reports.",
            "We turn location/activity data that already exists into an "
            "operations screen anyone can check.",
            "Dispatch, customer 'where is it' replies, and end-of-day reports from "
            "one live source.",
        ],
        "deliverables": [
            "Live tracking dashboard",
            "Status history + alerts",
            "Exportable reports",
        ],
        "saas_variant": "fleet/field-tracking SaaS (multi-client dashboards)",
    },
    "lead-gen-automation": {
        "angle": (
            "We build systems that turn public listings into a ranked pipeline of "
            "businesses to reach out to — no more guessing who to call."),
        "openers": [
            "Most {business} owners I meet rely on referrals and word of mouth "
            "to survive. That works until it stops.",
            "Noticed {business} doesn't seem to run a structured outreach "
            "pipeline — every enquiry probably arrives whenever it feels like it.",
            "{business} keeps growing, but I can tell new enquiries are mostly "
            "drift — nothing catches them systematically.",
        ],
        "hooks": [
            "I build automated lead-finding that feeds a clean follow-up queue, "
            "so no enquirer slips through.",
            "I can show you, from public data alone, roughly {{est}} potential "
            "customers in {area} you're currently not in front of.",
            "Instead of chasing, we can put a discovery-to-call pipeline in "
            "front of {business} — the CRM part is the easy bit.",
        ],
        "deliverables": [
            "Automated lead discovery from public listings",
            "CRM pipeline with dedupe + follow-up queue",
            "Personalised outreach drafts (human-approved)",
        ],
        "saas_variant": "multi-tenant lead-discovery + outreach-pipeline SaaS",
    },
    "digital-presence-booking": {
        "angle": (
            "We ship a mobile-first website with online booking and local search "
            "visibility, so customers can find and book without calling."),
        "openers": [
            "{business} — when someone searches for what you do in {area}, they "
            "land on competitors who let them book online.",
            "Right now {business} captures zero demand from search because there's "
            "no proper website or booking flow.",
            "Every booking for {business} currently goes through the phone — which "
            "means you're losing everyone who searches instead of calls.",
        ],
        "hooks": [
            "I build a fast booking site + local SEO; days 1-5 you see calls "
            "start to shift to bookings.",
            "A mobile-first site with a booking link is the single highest-ROI "
            "thing a {area} business can add to capture search demand.",
            "We can ship this in ~2 weeks: website, booking, Google Business "
            "profile alignment, analytics.",
        ],
        "deliverables": [
            "Mobile-first website",
            "Online booking / enquiry funnel",
            "Local SEO (Google Business profile, maps)",
            "WhatsApp scheduling links",
        ],
        "saas_variant": "bookable local-business website platform (per-vertical demo sites)",
    },
    "custom-web-application": {
        "angle": (
            "We build the internal or customer-facing tool a business actually "
            "runs on — tailored to its real process, not off-the-shelf limits."),
        "openers": [
            "Most internal tools force {business} to change how it works. That's "
            "backwards.",
            "If {business} keeps patching together spreadsheets and generic apps, "
            "the process is being decided by the software — not by the business.",
            "I'd bet the people inside {business} have a better way to work than "
            "the tools they're using today.",
        ],
        "hooks": [
            "I build a purpose-fit app around exactly how {business} works — "
            "database, UI, roles, deployment.",
            "Give me the messy process; the deliverable is the tool that removes "
            "the mess.",
            "We scope in a short workshop and ship incrementally — you see value "
            "in weeks, not quarters.",
        ],
        "deliverables": [
            "Purpose-fit web application (React / FastAPI)",
            "Database schema + auth & roles",
            "Incremental delivery with deployment",
        ],
        "saas_variant": "vertical-specific workflow products re-sold across an industry",
    },
    "hiring-onboarding-platform": {
        "angle": (
            "We turn candidate/screening/onboarding chaos into structured pipelines "
            "with pay-equity tooling where it matters."),
        "openers": [
            "{business} — hiring looks like it runs on email threads and "
            "spreadsheets. That's where good candidates get lost.",
            "Every unfilled seat costs {business} money it can't see; a structured "
            "pipeline fixes more than the process.",
            "Are you still tracking applicants and onboarding in separate tools? "
            "That data fragmentation is fixable.",
        ],
        "hooks": [
            "I build candidate pipelines, offer/onboarding workflows, and pay-band "
            "tooling that make hiring auditable and fair.",
            "A single pipeline for applicants → offers → onboarding — with "
            "structured decisions at every step.",
            "We've built a hiring stack before; it's not a research project, it's "
            "a rollout.",
        ],
        "deliverables": [
            "Applicant pipeline + scorecards",
            "Offer / onboarding automation",
            "Pay-band equity tooling",
        ],
        "saas_variant": "hiring / onboarding workflow SaaS with fairness layer",
    },
    "ai-powered-tools": {
        "angle": (
            "We put LLMs inside existing workflows for drafting, classification, "
            "and extraction — with a human review step built in."),
        "openers": [
            "{business} — if staff re-type or re-read the same things daily, "
            "that's hours an LLM can compress with review.",
            "There's a class of work at {business} that's reading + typing. "
            "That's exactly what an AI layer can carry.",
            "You don't need a chatbot; you need the repetitive part of the job "
            "done with a human approving the output.",
        ],
        "hooks": [
            "I build LLM-powered drafting, classification, and extraction into "
            "your current tools — with guardrails and logging.",
            "AI tooling isn't build vs buy; it's targeted flows where it earns "
            "its keep. We only ship the ones that do.",
            "A small, reviewed AI workflow can cut hours of busisness-daily "
            "reading and typing.",
        ],
        "deliverables": [
            "Targeted LLM flows (draft / classify / extract)",
            "Prompt + config library",
            "Human-review UI with guardrails & logging",
        ],
        "saas_variant": "domain-specific AI document/operator assistant SaaS",
    },
    "inventory-stock-automation": {
        "angle": (
            "We track stock across locations in real time with reorder alerts so "
            "nothing runs out and nothing rots."),
        "openers": [
            "{business} — if stock is counted on paper or in a spreadsheet, you "
            "are eating losses without seeing them.",
            "Every stock-out and every dead shelf means cash sitting still. Do "
            "you know exactly what's on hand right now?",
            "Inventory that's tracked in a spreadsheet is invisible; that's the "
            "gap we close.",
        ],
        "hooks": [
            "Real-time stock, reorder thresholds, supplier pricing — on one "
            "screen, on any device.",
            "We make the 'am I out?' question answerable in under a second, "
            "with alerts before you're out.",
            "Attach supplier records and you get forecasting-grade data without "
            "buying an enterprise ERP.",
        ],
        "deliverables": [
            "Live stock tracking",
            "Reorder / low-stock alerts",
            "Supplier & pricing records + reporting",
        ],
        "saas_variant": "inventory-management SaaS for growing retail/food verticals",
    },
    "billing-payments-automation": {
        "angle": (
            "We automate invoices, receipts, pending-dues follow-ups so money "
            "reconciles with what was billed."),
        "openers": [
            "{business} — if invoices are made by hand, someone is also chasing "
            "dues by hand. Both leak revenue.",
            "Recurring invoices and receipts typed manually mean pending money "
            "is almost never reconciled.",
            "The billing gap at {business} probably isn't rates; it's never "
            "billing what was actually delivered, on time.",
        ],
        "hooks": [
            "Auto-generated invoices/receipts, payment tracking, and automated "
            "dues follow-up — tax-ready records included.",
            "Every unpaid line item gets a reminder without anyone typing it.",
            "We make reconciliation a report instead of a day of work.",
        ],
        "deliverables": [
            "Invoice generation + receipts",
            "Payment tracking + pending-dues follow-up",
            "Tax-ready records",
        ],
        "saas_variant": "billing/payments operator SaaS per industry vertical",
    },
    "retention-referral-loyalty": {
        "angle": (
            "We reward repeat customers, flag who's about to churn, and turn "
            "happy customers into a referral engine."),
        "openers": [
            "{business} — most of the revenue already sits with repeat customers. "
            "Are they being rewarded?",
            "Every vertical loses customers quietly. {business} has no way to see "
            "who's slipping or who'd refer.",
            "Loyalty that lives in goodwill is luck; measured loyalty is a "
            "pipeline.",
        ],
        "hooks": [
            "Points/visits tracking, referral links, churn warnings — all in one "
            "lightweight program.",
            "We turn your regulars into a measured referral channel instead of "
            "hoping.",
            "Churn alerts before a customer drifts: that's the retention graph we "
            "build.",
        ],
        "deliverables": [
            "Loyalty / points program",
            "Visit & spend tracking",
            "Referral links + churn warnings",
        ],
        "saas_variant": "local-business loyalty & referrals SaaS",
    },
    "multi-location-ops": {
        "angle": (
            "We give multi-branch operations one dashboard: inventory, staffing, "
            "sales, and alerts per location."),
        "openers": [
            "{business}, with multiple locations — is there one screen that "
            "shows all of them at once?",
            "Each branch probably runs independently; decisions become guesses "
            "when there's no single view.",
            "Multi-location growth usually outruns the ops visibility behind it.",
        ],
        "hooks": [
            "One operations hub across branches: stock, shifts, sales, and "
            "per-location alerts.",
            "We sync cross-location where it matters and keep independence where "
            "it's needed.",
            "Central alerts replace 'call every branch on Monday'.",
        ],
        "deliverables": [
            "Branch hierarchy + per-location dashboards",
            "Cross-location stock/roster sync",
            "Central alerts",
        ],
        "saas_variant": "multi-location ops console SaaS for chains/franchises",
    },
    "scheduling-rosters": {
        "angle": (
            "We give shift planning, leave, and roster swaps a home — done on a "
            "calendar everyone can open."),
        "openers": [
            "{business} — if rosters are managed in a group chat, swaps and "
            "leaves are being re-negotiated daily.",
            "Shift coverage shouldn't depend on who replied last in WhatsApp.",
            "The constant 'who's working when' at {business} is a solved problem; "
            "it's just not solved yet for you.",
        ],
        "hooks": [
            "A shift calendar with leave/swaps, coverage alerts, and "
            "payroll-ready hours export.",
            "We remove the every-shift negotiation loop from your ops.",
            "Employees check their own roster; managers see coverage at a glance.",
        ],
        "deliverables": [
            "Shift calendar",
            "Leave / swap requests + coverage alerts",
            "Payroll-ready hours export",
        ],
        "saas_variant": "roster/leave SaaS for shift-based industries",
    },
    "document-management": {
        "angle": (
            "We give records a searchable, permission-controlled home — no more "
            "digging through folders and chat."),
        "openers": [
            "{business} — how long does it take to find one contract from last "
            "year? If the answer is 'minutes', you're losing time daily.",
            "Records that live in folders and chat are effectively lost.",
            "Every '{business} do you have the...' request is a search gone wrong.",
        ],
        "hooks": [
            "Upload + OCR indexing, full-text search, permissions, audit trail.",
            "We make 'find the document' a search box instead of a memory game.",
            "Compliance gets easy when every record has an audit trail.",
        ],
        "deliverables": [
            "Upload + OCR/indexing + full-text search",
            "Permission levels + audit trail",
        ],
        "saas_variant": "document-management SaaS for paper-heavy verticals",
    },
    "customer-comms-automation": {
        "angle": (
            "We automate routine customer updates — reminders, order status, "
            "follow-ups — via WhatsApp/email, safely rate-limited."),
        "openers": [
            "{business} — staff sending the same reminder to every customer, one "
            "by one, is the costliest hour of the day.",
            "Routine updates shouldn't require a human to type them each time.",
            "Every missed reminder at {business} is a no-show later.",
        ],
        "hooks": [
            "Automated reminder/follow-up flows with per-customer opt-outs and "
            "send-rate limits, delivered via WhatsApp/email.",
            "Set it once; every customer gets the update without manual typing, "
            "and nobody gets spammed.",
            "We keep human-in-the-loop: drafts, approvals, and strict rate "
            "limits are the default.",
        ],
        "deliverables": [
            "Reminder / follow-up flows",
            "WhatsApp/email delivery with rate limits + opt-outs",
            "Response tracking",
        ],
        "saas_variant": "customer-reminder/communications SaaS (compliant by design)",
    },
    "reports-dashboards": {
        "angle": (
            "We pull scattered numbers into one live dashboard of the KPIs the "
            "owner actually checks."),
        "openers": [
            "{business} — if the weekly numbers live in three places, nobody has "
            "the real picture.",
            "Decisions are only as good as the weekly picture; right now quarters "
            "get decided on gut.",
            "There's a gap between operations and owners at {business} — it's the "
            "numbers nobody compiles.",
        ],
        "hooks": [
            "A live KPI dashboard with automated pulls and email/WhatsApp digests.",
            "We surface the handful of numbers you actually check, refreshed "
            "automatically.",
            "Reports become a glance, not a Friday chore.",
        ],
        "deliverables": [
            "KPI dashboard",
            "Automated data pulls + digests",
            "Exportable reports",
        ],
        "saas_variant": "lightweight ops-analytics SaaS for SMBs",
    },
    "field-service-jobs": {
        "angle": (
            "We give field jobs assignment, status, and closure tracking with a "
            "technician app in real time."),
        "openers": [
            "{business} — if field jobs are assigned over the phone and pictured "
            "from memory, completion tracking is fiction.",
            "Every 'where's the tech?' call at {business} is lost dispatch time.",
            "Field teams work better with a single source of truth for jobs.",
        ],
        "hooks": [
            "Job assignment, live status, technician mobile app, customer "
            "updates.",
            "Dispatch from one screen; see completion in real time.",
            "We give field teams a tool that replaces phone-tag coordination.",
        ],
        "deliverables": [
            "Job assignment + status tracking",
            "Technician mobile app",
            "Customer updates",
        ],
        "saas_variant": "field-service/job-tracking SaaS",
    },
}


def outreach_for_solution(slug):
    """Return the outreach angle/opener/hook/deliverable templates for a slug."""
    if slug in OUTREACH_ANGLES:
        return OUTREACH_ANGLES[slug]
    return {
        "fallback": True,
        "angle": "Custom build tailored to the observed gap.",
        "openers": [f"{slug} looks like a fit for the problem observed."],
        "hooks": ["I build exactly this."],
        "deliverables": ["Scoped custom build"],
        "saas_variant": None,
    }


def offerings_list():
    """All sellable offerings: slug, angle, deliverables, SaaS variant."""
    return [
        {
            "solution_slug": slug,
            "angle": data["angle"],
            "deliverables": data["deliverables"],
            "saas_variant": data["saas_variant"],
        }
        for slug, data in sorted(OUTREACH_ANGLES.items())
    ]


def render_outreach(slug, business_name, area, opener_ix=None, hook_ix=None):
    """Build a personalized outreach draft body for a business + solution.

    DRAFT ONLY: the caller decides whether to save it into email_drafts; actual
    sending still requires operator approval + a send-enabled account.
    """
    tpl = outreach_for_solution(slug)
    import random as _r
    opener_ix = opener_ix if opener_ix is not None else _r.randrange(len(tpl["openers"]))
    hook_ix = hook_ix if hook_ix is not None else _r.randrange(len(tpl["hooks"]))
    opener = tpl["openers"][opener_ix].format(
        business=business_name or "this business", area=area or "your area")
    hook = tpl["hooks"][hook_ix].format(
        business=business_name or "this business", area=area or "your area")
    body = f"{opener}\n\n{hook}\n\n{tpl['angle']}"
    if business_name and business_name not in body:
        body = f"For {business_name}.\n\n{body}"
    return {
        "solution_slug": slug,
        "angle": tpl["angle"],
        "body": body,
        "deliverables": tpl["deliverables"],
        "saas_variant": tpl["saas_variant"],
    }