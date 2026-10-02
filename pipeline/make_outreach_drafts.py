"""Generate per-lead tailored client-outreach pitches for email leads.

Uses real scraped observations (rating, reviews, area) + category-specific
offer framing. High-entropy variation per AGENTS anti-fingerprinting rule.
Only creates DRAFTS - nothing sends without explicit operator action.
"""
import sqlite3
import json
import random
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent if "__file__" in locals() else Path(r"C:\Users\hsing\clientfinder-v3\pipeline")
ROOT = PIPE.parent
sys.path.insert(0, str(ROOT))

from service_catalog.email import create_draft, list_accounts  # noqa: E402
from client_framing import frame_lead  # noqa: E402
from html_email_builder import build_html_body  # noqa: E402

ACC_ID = next(a["id"] for a in list_accounts() if a["from_email"] == "hsinghjayesh@gmail.com")
SIGN = ("Jayesh Singh\n+91 78218 16193 | hsinghjayesh@gmail.com\n"
        "hire2onboard.com | github.com/Jayesh-ux | linkedin.com/in/jayesh-dev | jayesh-ux.github.io/jayesh-singh")

CAT = {
    "Salon": "salon", "Beauty Parlour": "salon", "Hairdresser": "salon", "Day spa": "spa",
    "Spa": "spa", "Massage spa": "spa", "Spa and health club": "spa",
    "Dental clinic": "dental", "Dentist": "dental",
    "Gym": "gym", "Fitness center": "gym", "Physical fitness program": "gym",
    "Coaching Center": "coaching", "Education center": "coaching",
    "Interior designer": "interior", "Interior design": "interior",
    "Bakery and Cake Shop": "bakery", "Cake shop": "bakery",
    "Dry cleaner": "dryclean", "Laundry service": "dryclean", "Laundry": "dryclean",
    "Pest control service": "pest",
    "Real estate agency": "realestate", "Real estate agent": "realestate", "Real estate consultant": "realestate",
    "Transportation service": "logistics", "Logistics service": "logistics",
    "Trucking company": "logistics", "Warehouse": "logistics", "Freight Forwarding Agency": "logistics",
    "Air conditioning repair service": "repair", "Appliance repair service": "repair",
    "Repair service": "repair", "Refrigerator repair service": "repair", "Microwave oven repair service": "repair",
    "Car wash": "carwash",
}

import textwrap

def render(tmpl, **kw):
    return textwrap.dedent(tmpl).strip().format(**kw)

BODIES = {
    "salon": [
        "{name} has {reviews} Google reviews and a {rating} rating - that's real reputation.\n"
        "But the online side is carried on Instagram and phone calls: no booking link, no auto\n"
        "follow-up, no reminders.\n\n"
        "I build simple systems for salons that do three things: a booking page customers can\n"
        "reach from your Instagram and Google profile, WhatsApp confirmations, and automatic\n"
        "reminders so no-shows drop. I can put a working sample for {name} in front of you in\n"
        "two days and you keep it only if it's useful. Also open to a full-time role if that's\n"
        "a better fit for you.",
        "{name} runs on phone bookings. Every query becomes a call, every no-show eats a slot,\n"
        "and there is no record of who came or who's waiting. I automate the booking\n"
        "side - online calendar + WhatsApp + reminders - so your staff stop chasing clients.\n"
        "Free sample in 2 days, no commitment. Also happy to talk full-time work if that suits\n"
        "you better.",
    ],
    "spa": [
        "You're in {area} with {reviews} reviews on Google, yet bookings for {name} still\n"
        "happen over the phone. A massage spa lives and dies on appointment flow, and right now\n"
        "nobody sees availability until they call.\n\n"
        "I build booking systems for spas: live availability, prepaid slots (fewer ghost\n"
        "bookings), WhatsApp confirmations and reminders. I'll build a working sample in two\n"
        "days - you keep it only if you like it. And I'm open to full-time dev roles too if\n"
        "that fits better.",
    ],
    "dental": [
        "Patients in {area} trust {name} ({reviews} reviews), but your appointment request\n"
        "today goes through WhatsApp or a phone call - and those conversations are easily\n"
        "missed during the day.\n\n"
        "I build clinic booking systems: a page patients can book on in two taps, automatic\n"
        "confirmations, and reminders that cut no-shows. It also captures patient enquiries so\n"
        "none get lost. I can show you a working sample in 2 days, no commitment. Open to\n"
        "full-time work too if that's a better route.",
        "Dental clinics lose patients on the follow-up: someone enquires, staff forgets, call\n"
        "missed, patient books elsewhere. I automate enquiry capture + booking + reminders for\n"
        "{name}. Two-day working sample, no obligation. Also open to a full-time role.",
    ],
    "gym": [
        "A gym with {name}'s rating ({rating}, {reviews} reviews) should be seeing trial\n"
        "requests land automatically - instead they arrive as DMs and calls. I build a simple\n"
        "trial-booking + membership enquiry system for gyms: form, WhatsApp auto-reply, and a\n"
        "lead log so no trial request slips. Two-day sample, keep it only if useful. Open to\n"
        "full-time too.",
        "{name} has the review credibility. What's missing is a funnel: people should fill a\n"
        "trial form, get an instant WhatsApp confirmation, and show up. I automate that.\n"
        "Deliverable sample in 2 days, no commitment. Or I'm open to a full-time dev role.",
    ],
    "coaching": [
        "Admissions for {name} depend on parents calling in. Every enquiry that isn't answered\n"
        "same-day is a lost seat. I build enquiry-capture + WhatsApp auto-reply + follow-up\n"
        "reminder systems for coaching centres, so every call gets logged and every parent\n"
        "gets a callback.\n\n"
        "I can put a working sample in front of you in two days. Also open to full-time\n"
        "opportunities if that's a better path.",
    ],
    "interior": [
        "Designers in {area} win or lose projects in the first response. {name} has the\n"
        "portfolio and reviews, but enquiries sit in WhatsApp with no schedule, no follow-up,\n"
        "and no pipeline.\n\n"
        "I build portfolio sites + enquiry systems with automated replies, so every lead is\n"
        "captured and followed up. Happy to build a live sample in two days - keep it only if\n"
        "it feels right. Also open to full-time roles.",
    ],
    "bakery": [
        "{name} gets orders over the phone while customers scroll Google. I build a simple\n"
        "order/booking page that shows on your Google profile - order form, WhatsApp\n"
        "confirmation, and an order log. Two-day sample or open to full-time work.",
    ],
    "dryclean": [
        "Pickup/delivery services like {name} run on manual WhatsApp threads. I automate\n"
        "order capture + confirmation + reminders. Two-day sample, no commitment.",
    ],
    "pest": [
        "Pest control enquiries are time-sensitive - someone with a termite problem calls\n"
        "three companies. {name} needs every enquiry answered instantly. I build enquiry\n"
        "capture + auto-reply + callback logging. Working sample in 2 days. Open to full-time\n"
        "too.",
    ],
    "realestate": [
        "Property enquiries disappear in personal chats. I build lead capture + WhatsApp\n"
        "auto-reply + follow-up reminders for {name} so every buyer/seller gets a fast\n"
        "response. 2-day sample, no obligation.",
    ],
    "logistics": [
        "Freight and transport quotes are daily, repeatable, and eaten up by manual\n"
        "follow-ups. I build enquiry->quote follow-up automation for {name}: capture, instant\n"
        "acknowledgement, reminder sequences. Working sample in two days. Open to full-time\n"
        "roles too.",
        "Transports get quotes over call and lose them to follow-up. I automate the enquiry "
        "follow-up loop for {name}. 2-day sample, no commitment.",
    ],
    "repair": [
        "Repair jobs are logged in chat and follow-ups get forgotten. I build job-capture +\n"
        "status-update automation so {name} never loses a ticket. Working sample in 2 days,\n"
        "keep it only if useful.",
    ],
    "carwash": [
        "{name} could pre-sell car-care plans instead of waiting for walk-ins. I build a\n"
        "booking + membership page with WhatsApp confirmation. 2-day sample, no commitment.",
    ],
}

SUBJECTS = {
    "salon": ["Sales appointments for {name}", "Booking system for {name}", "Saving {name} missed bookings"],
    "spa": ["Online bookings for {name}", "{name} - appointments on autopilot"],
    "dental": ["Bookings for {name}", "Missed patient enquiries at {name}", "Scheduling system for {name}"],
    "gym": ["Trial bookings for {name}", "Membership leads for {name}"],
    "coaching": ["Enquiry follow-up for {name}", "Admissions system for {name}"],
    "interior": ["Enquiries for {name}", "Portfolio + lead system for {name}"],
    "bakery": ["Online orders for {name}", "Order system for {name}"],
    "dryclean": ["Order automation for {name}", "Pickup orders for {name}"],
    "pest": ["Faster replies for {name}", "Pest enquiry capture for {name}"],
    "realestate": ["Lead capture for {name}", "Enquiry responses for {name}"],
    "logistics": ["Quote follow-up automation for {name}", "Enquiry system for {name}"],
    "repair": ["Job capture for {name}", "Service tickets for {name}"],
    "carwash": ["Pre-paid car care for {name}", "Booking page for {name}"],
}


def parse_extras(notes):
    if notes and "; " in notes:
        try:
            return json.loads(notes.split("; ", 1)[1])
        except Exception:
            return {}
    return {}


def main():
    c = sqlite3.connect(str(PIPE / "crm.db"))
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "select * from leads where public_business_email is not null and public_business_email != ''"
        " and not exists (select 1 from email_drafts d where d.lead_id = leads.lead_id)"
    ).fetchall()

    created = 0
    for r in rows:
        name = (r["business_name"] or "").split(" | ")[0].strip()
        cat_key = CAT.get(r["business_category"])
        if not name:
            continue
        ex = parse_extras(r["notes"])
        rating = ex.get("rating")
        reviews = ex.get("reviews_count")
        rating_s = f"{rating}" if rating not in (None, "", "N/A") else "top"
        reviews_s = f"{reviews}" if reviews not in (None, "", 0) else "strong"
        area = (r["area"] or r["city"] or "Mumbai").strip()
        try:
            name_short = name.split()[0]
        except Exception:
            name_short = name

        f = frame_lead(r)
        if cat_key:
            bodies = BODIES[cat_key]
            body = render(random.choice(bodies), name=name, rating=rating_s, reviews=reviews_s, area=area)
        else:
            # Frame-based fallback: any category not in the BODIES map gets a
            # structure identical to the curated ones (problem/tension/solution).
            body = (f"{name} has {reviews_s} Google reviews and a {rating_s} rating - that's real reputation.\n"
                    f"But enquiries still come in by call and WhatsApp: {f['problem']}.\n\n"
                    f"This quietly costs you: {f['tension']}.\n\n"
                    f"The fix is {f['solution']} - I can put a working sample for {name} in front of you in two days, "
                    "and you keep it only if it's useful. Also open to a full-time role if that's a better fit.")
        body += "\n\nWorth a 10-minute call this week?\n\n" + SIGN
        subj = random.choice(SUBJECTS[cat_key] if cat_key else ["Business enquiries for {name}", "{name} - stopping missed enquiries"]).format(name=name[:70])

        html_body = build_html_body(f, subj, body, business_email=r["public_business_email"] or "")

        d = create_draft({
            "lead_id": r["lead_id"],
            "solution_slug": r["recommended_offer"] or None,
            "account_id": ACC_ID,
            "subject": subj,
            "body": body,
            "html_body": html_body,
            "tags": "client-outreach,draft-v2,email-found,html",
        })
        created += 1
        print(f"draft {d['id']} | {subj}")

    c.close()
    print(f"created {created} drafts")


if __name__ == "__main__":
    main()