import sqlite3
import json
import re
import csv

DB = r"C:\Users\hsing\clientfinder-v3\pipeline\crm.db"
OUT = r"C:\Users\hsing\clientfinder-v3\pipeline\all_leads_export.csv"

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute("select * from leads order by business_name").fetchall()
cols = [r[1] for r in c.execute("pragma table_info(leads)").fetchall()]

# ---------------------------------------------------------------------------
# Category -> (typical problem profile, deliverable angle)
# Honest: used ONLY when that lead has no scraped observation fields.
# ---------------------------------------------------------------------------
CAT = {
    "Interior designer": ("no branded website/portfolio to win big projects", "portfolio site + online booking + review-led local SEO"),
    "Dental clinic": ("no online booking; patients still call during business hours", "booking + reminder + Google reviews engine"),
    "Transportation service": ("no quote form; inquiries go through calls only", "quote-request website + WhatsApp to lead them back"),
    "Beauty Parlour": ("no online booking; walk-ins lost & no rebooking", "booking page + Instagram-linked booking + review push"),
    "Gym": ("no online signup; free-trial enquiries leak", "signup + trial-booking funnel + payment link"),
    "Bakery and Cake Shop": ("orders still by call/WhatsApp list; no product page", "order-form site + WhatsApp catalog + online payment"),
    "Coaching Center": ("admission enquiries only on call; no batch info online", "admission-enquiry funnel + batch listing + class demo booking"),
    "Appliance repair service": ("no online booking; emergency calls lost", "instant booking + job-status tracking + repeat-customer SMS"),
    "Cafe": ("no online ordering/table booking; footfall only", "order/booking site + Google visibility + loyalty QR"),
    "Boutique": ("no online catalog/trial booking; IG-only presence", "catalog site + trial-appointment booking + payment"),
    "Spa": ("no online slot booking; phone-only scheduling", "slot-booking + package pricing + review engine"),
    "Courier service": ("no online rate/order form; quotes by phone", "rate calculator + pickup-booking form"),
    "Car wash": ("no online slot booking/queue; peak-hour drop-offs", "slot-booking + subscription pack + feedback loop"),
    "Hairdresser": ("no online booking; walk-in dependent", "booking + reminder + before/after gallery"),
    "Clothing store": ("no online catalog/delivery; stock by visit only", "store-front site + WhatsApp catalog + delivery option"),
    "Air conditioning repair service": ("no online booking; no technician tracking", "booking + service-tracking + AMC lead capture"),
    "Warehouse": ("no online enquiry form; capacity by call only", "capacity enquiry form + postcode-based search"),
    "Cake shop": ("orders by call; no advance-ordering page", "pre-order form + occasion calendar + online payment"),
    "North Indian restaurant": ("no online table booking/ordering; busy phone during peak", "table-booking + online order + Google listing fix"),
    "Dentist": ("no online appointment; clinic hours lose patients", "appointment booking + reminder + Google reviews"),
    "Security guard service": ("no online quote form; B2B enquiries by call", "quote form + compliance/credibility page"),
    "Shipping service": ("no online quote/tracking for shippers", "online quote + tracking lookup page"),
    "Pest control service": ("no online booking; emergency calls lost", "quick-quote + booking + AMC lead capture"),
    "Moving service": ("no online quote/estimate; comparisons by call", "estimate form + transparent pricing page"),
    "Massage spa": ("no online slot booking; no packages shown", "slot booking + package page + review push"),
    "Fitness center": ("no online signup; trial enquires leak", "signup + trial funnel + payments"),
    "Tailor": ("no order form/catalog; alterations by visit", "custom-order form + measurement guide"),
    "Repair service": ("no online booking; calls lost off-hours", "booking + tracking + AMC capture"),
    "Moving and storage service": ("no online estimate; only phone quotes", "estimate form + storage pricing page"),
    "Italian restaurant": ("no online reservation/ordering", "reservation + online-order page"),
    "Designer Clothing Store": ("no online catalog; IG-only", "catalog + trial booking + payment"),
    "Auto repair shop": ("no online booking; drop-off only", "booking + job tracking + warranty page"),
    "Washer & dryer repair service": ("no online booking; no technician tracking", "booking + job tracking + AMC"),
    "Trucking company": ("no online quote/order form", "quote form + fleet/credibility page"),
    "South Indian restaurant": ("no online ordering/booking", "online order + reservation"),
    "Restaurant": ("no online booking/ordering", "reservation + online order"),
    "Refrigerator repair service": ("no online booking; emergency calls lost", "booking + tracking + AMC"),
    "Real estate agency": ("no lead-capture funnel; follow-ups leak", "property listing site + lead-capture + auto-followup"),
    "Mughlai restaurant": ("no online ordering/booking", "online order + reservation"),
    "Men's clothing store": ("no online catalog/delivery", "catalog + WhatsApp catalog + delivery"),
    "Logistics service": ("no online quote/order form", "quote form + tracking page"),
    "Laundry service": ("no online pickup/order; only counter visits", "pickup-order form + schedule + payment"),
    "Indian sweets shop": ("no online pre-order; festive orders by phone", "pre-order + festive campaign + payment"),
    "Indian restaurant": ("no online booking/ordering", "online order + reservation"),
    "Hair salon": ("no online booking; walk-in dependent", "booking + reminder + gallery"),
    "Gastropub": ("no online table booking; weekend walk-ins risky", "table booking + event page"),
    "Freight Forwarding Agency": ("no online quote form; B2B by email/call", "quote form + credibility/tracking page"),
    "Education center": ("no admission-enquiry funnel", "admission funnel + batch info + demo booking"),
    "Dry cleaner": ("no online pickup/order; counter only", "pickup-order + schedule + loyalty"),
    "Day spa": ("no online slot booking", "slot booking + packages page"),
    "Vegetarian restaurant": ("no online ordering/booking", "online order + reservation"),
    "Sweet shop": ("no online pre-order; festive orders by phone", "pre-order + gift-pack page + payment"),
    "Spa and health club": ("no online membership/enrolment", "membership page + signup funnel"),
    "Self-storage facility": ("no online enquiry/booking", "enquiry form + size/pricing page"),
    "Seafood restaurant": ("no online ordering/booking", "online order + reservation"),
    "Salon": ("no online booking; walk-in dependent", "booking + reminder + before/after gallery"),
    "Real estate consultant": ("no CRM funnel; follow-ups leak", "listing site + lead capture + auto-followup"),
    "Real estate agent": ("no lead-capture funnel on listings", "listing site + lead forms + followup"),
    "Pressure washing service": ("no online quote/booking", "quote + booking + before/after proof"),
    "Physical fitness program": ("no online signup/trial funnel", "signup + trial funnel"),
    "Packaging company": ("no online quote form; B2B by call", "quote form + capability page"),
    "Microwave oven repair service": ("no online booking; calls lost off-hours", "booking + tracking + AMC"),
    "Laundry": ("no online pickup/order", "pickup-order + schedule + payment"),
    "Japanese restaurant": ("no online ordering/booking", "online order + reservation"),
    "Interior design": ("no branded portfolio site", "portfolio + enquiry funnel"),
    "Industrial real estate agency": ("no digital lead capture", "listing + lead form + followup"),
    "Gents Tailor": ("no order form/catalog", "custom-order form + measurement guide"),
    "Fast food restaurant": ("no online ordering", "online order + combos page"),
    "Family restaurant": ("no online booking/ordering", "reservation + online order"),
    "Eyebrow bar": ("no online slot booking", "slot booking + packages + review push"),
    "Doctor": ("no online appointment; OPD hours constrain", "appointment booking + reminder + reviews"),
    "Customs broker": ("no online quote form; B2B by email", "quote form + compliance/credibility page"),
    "Corporate office": ("no online enquiry/careers funnel", "enquiry + careers page + credibility"),
    "Continental restaurant": ("no online ordering/booking", "online order + reservation"),
    "Commercial real estate agency": ("no lead-capture on listings", "listing + lead forms + followup"),
    "Car detailing service": ("no online booking; detailing drop-off only", "slot booking + package page + before/after proof"),
    "Bistro": ("no online booking/ordering", "reservation + online order"),
    "Bar": ("no online table/reservation", "table booking + event page"),
    "Back Office": ("no digital service/credibility page", "services page + enquiry funnel"),
    "Auto restoration service": ("no online booking/portfolio", "portfolio + booking"),
    "Asian restaurant": ("no online ordering/booking", "online order + reservation"),
}

GENERIC_PROBLEM = "no clean way for customers to enquire/book online - calls leak off-hours"
GENERIC_ANGLE = "simple website/booking flow + Google visibility + review engine"

# ---------------------------------------------------------------------------
# Extract rating + reviews_count from the JSON embedded in notes
# (format: "auto-imported from run_scrape.py; {json}")
# ---------------------------------------------------------------------------
def parse_notes(r):
    note = (r["notes"] or "")
    m = re.search(r"\{.*\}", note, re.S)
    rating = reviews = None
    if m:
        try:
            j = json.loads(m.group(0))
            rating = j.get("rating")
            reviews = j.get("reviews_count")
        except Exception:
            pass
    elif ":" not in note:  # the 3 Bengaluru seed notes are plain text
        pass
    return rating, reviews, note

# ---------------------------------------------------------------------------
def lead_problem(r):
    obs = [o.rstrip(".!?") for o in (
        (r["booking_observation"] or "").strip(),
        (r["conversion_observation"] or "").strip(),
        (r["social_activity_observation"] or "").strip(),
    ) if o and o.lower() not in ("none", "n/a", "-")]
    if obs:
        return obs[0] + (". " + obs[1][0].lower() + obs[1][1:] if len(obs) > 1 else ".")
    cat = (r["business_category"] or "").strip()
    return CAT.get(cat, (GENERIC_PROBLEM,))[0].capitalize() + "."

def lead_angle(r):
    cat = (r["business_category"] or "").strip()
    return CAT.get(cat, (None, GENERIC_ANGLE))[1]

def lead_why(r):
    rating, reviews, _ = parse_notes(r)
    cat = (r["business_category"] or "").strip()
    area = (r["area"] or "").strip()
    site = (r["website_url"] or "").strip()
    angle = lead_angle(r)

    bits = []
    if rating:
        rv = f", {reviews} reviews" if reviews else ""
        bits.append(f"already pulling ~{rating}-star ratings{rv} on their Google listing")
    if not site:
        bits.append("no website showing in local Google searches")
    if bits:
        _, _, note = parse_notes(r)
        if "Frustrated" in note or "frustrated" in note:
            bits.append("already frustrated with phone-only operations (their own words)")
    ctx = "; ".join(bits) if bits else f"{cat} with no working online funnel in {area or 'Mumbai'}"

    return (f"They keep getting calls, but none turn into trackable, repeatable business - and their "
            f"online presence has gaps ({ctx}). That combination is exactly what a "
            f"{angle} fixes: we build it for them, they only pay after they see bookings "
            f"they can actually count. Cost to them is a fraction of what one walk-in "
            f"customer is worth.")

# ---------------------------------------------------------------------------
NEW_COLS = ["lead_problem", "why_they_pay_us"]
out_cols = cols + NEW_COLS

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(out_cols)
    for r in rows:
        w.writerow([r[col] for col in cols] + [lead_problem(r), lead_why(r)])

print(f"updated {OUT} -> {len(rows)} rows, {len(out_cols)} cols")
print("\nsamples:")
for name in ["Sri Balaji Dental Studio", "Waves Gym", "32Smiles", "Home Makers Interior", "24 x 7 AC Repair"]:
    r = next((x for x in rows if x["business_name"].startswith(name)), None)
    if r:
        print(f"\n- {r['business_name']} [{r['business_category']}]")
        print(f"  PROBLEM: {lead_problem(r)}")
        print(f"  WHY PAY: {lead_why(r)}")