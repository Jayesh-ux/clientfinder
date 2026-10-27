"""Rank leads by visible revenue leak, so outreach targets the few that are ready.

Running the daily scrape fills the CRM with every business it finds. Most of them
are not worth a phone call: low review counts, a perfectly good website, or a
category where online booking does not apply. Contacting them is how you burn a
week for nothing.

This scores on the signals that indicate money is already being lost:

  - review count       -> proof of real, paying demand. 200 reviews is a business
                          that loses money every month it drops enquiries.
  - owner-operated     -> no site and no generic email, so the owner personally
                          answers (or misses) every enquiry. This identifies WHO
                          you are talking to. It is not a gap to be filled with a
                          website: these businesses have run without one for
                          years, and asking for one reads as a tech sales pitch.
  - impulsive enquiries -> categories where people decide on the spot and expect
                          a reply now (salon, gym, AC repair, cake order).
  - reachable by phone -> you can actually walk in or dial today.

A high score means "the owner is losing enquiries right now and can prove it".
Low score means "busy, or already sorted, or nobody to talk to".

The fix offered is always WhatsApp first - a channel the owner already keeps open
all day - with no site, no hosting, and no monthly fee.

Usage:
    python pipeline/rank_by_leak.py                 # print top 25 walk-in list
    python pipeline/rank_by_leak.py --limit 40
    python pipeline/rank_by_leak.py --apply          # write priority + offer to CRM
    python pipeline/rank_by_leak.py --csv data/outreach/walkin_sheet.csv
"""

import argparse
import csv
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service_catalog.config import get_db_path  # noqa: E402

# Categories where an online booking/order/enquiry flow is genuinely expected by
# customers. For these, a missing booking path is a real leak rather than noise.
BOOKING_RELEVANT = {
    "Dental clinic", "Dentist", "Salon", "Beauty Parlour", "Hairdresser",
    "Spa", "Day spa", "Massage spa", "Spa and health club", "Gym",
    "Fitness center", "Physical fitness program", "Coaching Center",
    "Education center", "Interior designer", "Interior design",
    "Bakery and Cake Shop", "Cake shop", "Boutique", "Eyebrow bar",
    "Car wash", "Dry cleaner", "Laundry service", "Laundry",
    "Pest control service", "Appliance repair service", "Air conditioning repair service",
    "Refrigerator repair service", "Repair service", "Real estate agency",
    "Real estate agent", "Real estate consultant",
}

OFFER = {
    "Dental clinic": "WhatsApp booking that confirms the slot instantly and reminds "
                     "the patient the night before, so booked patients stop turning into no-shows",
    "Dentist": "WhatsApp booking that confirms the slot instantly and reminds the patient "
               "the night before, so booked patients stop turning into no-shows",
    "Salon": "WhatsApp booking on the number you already take calls on, with automatic "
             "reminders, so the gaps in your diary stop showing up as empty slots",
    "Beauty Parlour": "WhatsApp booking on the number you already take calls on, with "
                      "automatic reminders, so the gaps in your diary stop showing up as empty slots",
    "Hairdresser": "WhatsApp booking on the number you already take calls on, with automatic "
                   "reminders, so the gaps in your diary stop showing up as empty slots",
    "Spa": "WhatsApp booking with a reminder the day before, so no-shows and "
           "double-booked slots stop",
    "Day spa": "WhatsApp booking with a reminder the day before, so no-shows and "
               "double-booked slots stop",
    "Massage spa": "WhatsApp booking with a reminder the day before, so no-shows and "
                   "double-booked slots stop",
    "Spa and health club": "WhatsApp booking with a reminder the day before, so no-shows "
                           "and double-booked slots stop",
    "Gym": "a WhatsApp auto-reply that answers instantly when someone asks about trials or "
           "timings, so an enquiry gets a reply in seconds instead of tomorrow",
    "Fitness center": "a WhatsApp auto-reply that answers instantly when someone asks about "
                      "trials or timings, so an enquiry gets a reply in seconds instead of tomorrow",
    "Physical fitness program": "a WhatsApp auto-reply that answers instantly when someone "
                                "asks about trials or timings, so an enquiry gets a reply in seconds",
    "Coaching Center": "WhatsApp enquiry capture with an instant reply and a same-day callback "
                       "reminder, so every parent's question gets answered the same day",
    "Education center": "WhatsApp enquiry capture with an instant reply and a same-day callback "
                        "reminder, so every parent's question gets answered the same day",
    "Interior designer": "WhatsApp enquiry capture that replies the moment an enquiry arrives, "
                         "plus a simple gallery you can send in the chat. No website needed",
    "Interior design": "WhatsApp enquiry capture that replies the moment an enquiry arrives, "
                       "plus a simple gallery you can send in the chat. No website needed",
    "Bakery and Cake Shop": "a WhatsApp menu with a payment link, so cake orders come in with "
                            "the date and message attached instead of as a missed call",
    "Cake shop": "a WhatsApp menu with a payment link, so cake orders come in with the date "
                 "and message attached instead of as a missed call",
    "Boutique": "a WhatsApp catalogue with a payment link, so orders happen in the chat "
                "without anyone needing to visit first",
    "Eyebrow bar": "WhatsApp booking with reminders, so the gaps in your afternoon diary are "
                   "actually filled",
    "Car wash": "WhatsApp enquiry handling plus a monthly-plan reminder message, so regular "
                "cars come back on a schedule instead of you hoping they remember",
    "Dry cleaner": "WhatsApp pickup and delivery confirmation, so the collection slot is agreed "
                   "in the chat instead of over a call you keep missing",
    "Laundry service": "WhatsApp pickup and delivery confirmation, so the collection slot is "
                       "agreed in the chat instead of over a call you keep missing",
    "Laundry": "WhatsApp pickup and delivery confirmation, so the collection slot is agreed in "
               "the chat instead of over a call you keep missing",
    "Pest control service": "an instant WhatsApp reply that qualifies the job and books the visit, "
                            "because whoever answers first gets the termite call",
    "Appliance repair service": "WhatsApp job capture that collects the model, address and problem "
                                "before you dial, and sends the visit status automatically",
    "Air conditioning repair service": "WhatsApp job capture that collects the model, address and "
                                       "problem before you dial, and sends visit status automatically",
    "Refrigerator repair service": "WhatsApp job capture that collects the model, address and "
                                   "problem before you dial, and sends visit status automatically",
    "Repair service": "WhatsApp job capture that collects the model, address and problem before "
                      "you dial, and sends the visit status automatically",
    "Real estate agency": "WhatsApp lead capture with an instant reply, so a buyer who messages "
                          "at 11pm is still a lead in the morning instead of a lost one",
    "Real estate agent": "WhatsApp lead capture with an instant reply, so a buyer who messages "
                         "at 11pm is still a lead in the morning instead of a lost one",
    "Real estate consultant": "WhatsApp lead capture with an instant reply, so a buyer who "
                               "messages at 11pm is still a lead in the morning instead of a lost one",
}

DEFAULT_OFFER = ("a WhatsApp auto-reply that answers enquiries the moment they arrive, so you "
                 "stop losing the ones that come while you're on a job")
BOOKING_HINT = re.compile(
    r"book|appoint|reserv|order|enquir|contact|whatsapp|schedule|slot|checkout|cart",
    re.I,
)


def parse_extras(notes):
    if not notes:
        return {}
    m = re.search(r"\{.*\}", notes, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except (json.JSONDecodeError, ValueError):
        return {}


def to_int(value):
    try:
        return int(str(value).strip().split(",")[0])
    except (TypeError, ValueError):
        return 0


def clean_phone(phone):
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits


def score_lead(row):
    """0-100. Higher = more obviously losing money, and reachable today."""
    ex = parse_extras(row["notes"])
    reviews = to_int(ex.get("reviews_count"))
    site = (row["website_url"] or "").strip()
    email = (row["public_business_email"] or "").strip()
    phone = clean_phone(row["public_business_phone"])
    category = (row["business_category"] or "").strip()
    booking_relevant = category in BOOKING_RELEVANT

    score = 0
    reasons = []

    # Demand proof on a real log scale: the jump from 5 to 50 reviews matters far
    # more than 500 to 520, and 9000 reviews is not 40x better than 200.
    if reviews:
        score += min(40, int(40 * math.log10(reviews + 1) / math.log10(1001)))
        if reviews >= 100:
            reasons.append(f"{reviews} reviews = proven demand")
        elif reviews >= 30:
            reasons.append(f"{reviews} reviews")

    # Owner-operated means the owner personally answers (or doesn't) the
    # enquiries, and that WhatsApp is already the live channel. This is a signal
    # about who you're talking to, NOT a gap that needs a website filling it.
    if not site and not email:
        score += 15
        reasons.append("owner-run: no site, no email, enquiries land on WhatsApp/phone")
    elif not site:
        score += 12
        reasons.append("owner-run: no site")
    elif not BOOKING_HINT.search(site):
        score += 8 if booking_relevant else 4
        reasons.append("site has no booking/order/enquiry path")

    # Walk-in traffic means enquiries are impulsive and time-of-day dependent,
    # which is exactly where an instant WhatsApp reply converts and a missed
    # call does not.
    if booking_relevant:
        score += 12
        reasons.append("impulsive enquiries; instant reply converts")
    if phone:
        score += 10
        reasons.append("phone on file: walk in or dial")
    else:
        score -= 25
        reasons.append("no phone: walk-in only")

    # A gmail address usually means the listing is owner-run and unmaintained.
    if email.endswith("@gmail.com") or email.endswith("@yahoo.com"):
        score += 5
        reasons.append("personal email on the listing")

    if (row["do_not_contact"] or 0) == 1:
        return 0, ["do_not_contact flag set"], reviews, phone, ""

    return score, reasons, reviews, phone, OFFER.get(category, DEFAULT_OFFER)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=25, help="rows to show")
    ap.add_argument("--min-score", type=int, default=45)
    ap.add_argument("--apply", action="store_true",
                    help="write priority/offer/personalisation into the CRM")
    ap.add_argument("--csv", help="also write the walk-in sheet to this CSV path")
    args = ap.parse_args()

    conn = sqlite3.connect(str(get_db_path()))
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(
        "select lead_id, business_name, business_category, area, city, address_public, "
        "website_url, public_business_email, public_business_phone, notes, do_not_contact "
        "from leads where do_not_contact is null or do_not_contact = 0"))

    scored = []
    for r in rows:
        score, reasons, reviews, phone, offer = score_lead(r)
        if score >= args.min_score:
            scored.append((score, r, reasons, reviews, phone, offer))
    scored.sort(key=lambda x: (-x[0], -x[3]))

    print(f"{len(scored)} of {len(rows)} leads clear score {args.min_score}\n")
    print(f"{'#':>3} {'score':>5}  {'business':38s} {'category':18s} {'area':12s}")
    for i, (score, r, reasons, reviews, phone, offer) in enumerate(scored[:args.limit], 1):
        where = (r["area"] or r["city"] or "-")[:12]
        print(f"{i:>3} {score:>5}  {r['business_name'][:38]:38s} "
              f"{(r['business_category'] or '-')[:18]:18s} {where:12s}")

    if args.apply:
        for score, r, _reasons, _reviews, _phone, offer in scored:
            note = f"leak_score={score} | " + "; ".join(_reasons)
            conn.execute(
                "update leads set lead_score=?, priority=?, recommended_offer=?, "
                "personalisation_note=?, first_contact_channel=? where lead_id=?",
                (score,
                 "high" if score >= 70 else "medium" if score >= 55 else "low",
                 offer, note,
                 "walk_in_or_phone" if clean_phone(r["public_business_phone"]) else "walk_in",
                 r["lead_id"]))
        conn.commit()
        print(f"\napplied priority + offer to {len(scored)} leads")

    if args.csv:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "leak_score", "business_name", "category", "area",
                        "address", "phone", "website", "email", "google_reviews",
                        "why_they_are_a_target", "one_line_offer"])
            for i, (score, r, reasons, reviews, phone, offer) in enumerate(scored[:args.limit], 1):
                w.writerow([i, score, r["business_name"], r["business_category"],
                            r["area"] or r["city"], r["address_public"], phone,
                            r["website_url"], r["public_business_email"], reviews,
                            "; ".join(reasons), offer])
        print(f"walk-in sheet -> {args.csv}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())