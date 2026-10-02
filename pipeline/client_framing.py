"""CLIENTFINDER - per-lead framing: PROBLEM / TENSION / SOLUTION.

Single source of truth for the "problem -> tension -> solution" approach used in
both intro emails and follow-ups. Works for ANY lead row (existing CRM leads or a
row dict produced by a future search) as long as it has the standard columns
(business_name, business_category, area, notes, booking_observation,
conversion_observation, social_activity_observation).

Nothing here sends anything - it only produces copy. Drafts stay drafts.
"""
import json
import re


def parse_extras(notes):
    """Return {rating, reviews_count, ...} from the JSON embedded in `notes`."""
    if not notes:
        return {}
    m = re.search(r"\{.*\}", notes, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}
    return {}


# ---------------------------------------------------------------------------
# PROBLEM: real observation first, else a category-accurate hypothesis.
# ---------------------------------------------------------------------------
OBSERVATION_COLS = (
    "booking_observation",
    "conversion_observation",
    "social_activity_observation",
)

CAT_PROBLEM = {
    "Interior designer": "no branded website/portfolio to win big projects",
    "Dental clinic": "no online booking; patients still call during business hours",
    "Dentist": "no online appointment; clinic hours lose patients",
    "Transportation service": "no quote form; inquiries go through calls only",
    "Beauty Parlour": "no online booking; walk-ins lost, no rebooking",
    "Gym": "no online signup; free-trial enquiries leak",
    "Bakery and Cake Shop": "orders by call/WhatsApp; no product page or pre-order flow",
    "Coaching Center": "admission enquiries only on call; no batch info online",
    "Education center": "no admission-enquiry funnel",
    "Appliance repair service": "no online booking; emergency calls lost",
    "Cafe": "no online ordering or table booking; footfall only",
    "Boutique": "no online catalog or trial booking; IG-only presence",
    "Spa": "no online slot booking; phone-only scheduling",
    "Courier service": "no online rate/order form; quotes by phone",
    "Car wash": "no online slot booking; peak-hour drop-offs",
    "Hairdresser": "no online booking; walk-in dependent",
    "Clothing store": "no online catalog or delivery; stock by visit only",
    "Air conditioning repair service": "no online booking; no technician tracking",
    "Warehouse": "no online enquiry form; capacity by call only",
    "Cake shop": "orders by call; no advance-ordering page",
    "North Indian restaurant": "no online table booking or ordering",
    "Security guard service": "no online quote form; B2B enquiries by call",
    "Shipping service": "no online quote or tracking for shippers",
    "Pest control service": "no online booking; emergency calls lost",
    "Moving service": "no online quote/estimate; comparisons by call",
    "Massage spa": "no online slot booking; no packages shown",
    "Fitness center": "no online signup; trial enquiries leak",
    "Tailor": "no order form or catalog; alterations by visit",
    "Repair service": "no online booking; calls lost off-hours",
    "Real estate agency": "no lead-capture funnel; follow-ups leak",
    "Hair salon": "no online booking; walk-in dependent",
    "Dry cleaner": "no online pickup/order; counter only",
    "Day spa": "no online slot booking",
    "Laundry service": "no online pickup/order; only counter visits",
    "Laundry": "no online pickup/order",
    "Car detailing service": "no online booking; detailing drop-off only",
    "Doctor": "no online appointment; OPD hours constrain",
}

GENERIC_PROBLEM = "no clean way for customers to enquire or book online - calls leak off-hours"

# ---------------------------------------------------------------------------
# TENSION: the cost of the problem in their terms.
# ---------------------------------------------------------------------------
CAT_TENSION = {
    "Interior designer": "design projects are won on first response - every enquiry left on WhatsApp with no schedule is a project that walks to the studio that replies first",
    "Dental clinic": "a patient who can't book tonight books with the clinic that can - and your own follow-up forgets the rest",
    "Dentist": "a patient who can't book tonight books with the clinic that can",
    "Transportation service": "every quote enquiry not answered instantly is a consignment your competitor wins",
    "Beauty Parlour": "every walk-in that can't see availability simply doesn't come - and nobody comes back twice without a reminder",
    "Gym": "the trial-seeker clicking your competitor's signup form is your lost membership",
    "Bakery and Cake Shop": "the festive-order window is short - orders lost to a busy phone line don't come back",
    "Coaching Center": "every parent enquiry not answered same-day is a seat your rival fills",
    "Education center": "every parent enquiry not answered same-day is a seat your rival fills",
    "Appliance repair service": "an emergency repair call that goes to voicemail goes to the next repairman online",
    "Cafe": "footfall-only means zero repeat business beyond whoever happens to walk in",
    "Boutique": "a customer who can't see new arrivals or book a trial visit simply forgets you",
    "Spa": "a booking that still requires a phone call gets abandoned mid-day - and no-shows are never recovered",
    "Courier service": "a quote that requires a call is a quote that never gets compared - or chosen",
    "Car wash": "peak-hour drop-offs without slots means long waits and walk-aways",
    "Hairdresser": "no-shows are never recovered and walk-ins can't see availability",
    "Clothing store": "you only exist to customers within walking distance when your mates can order from a competitor at midnight",
    "Air conditioning repair service": "an AC down in peak heat isn't a service call - it's an emergency, and emergencies go to whoever answers first online",
    "Warehouse": "capacity enquiries by phone means you're invisible exactly when a logistics manager Googles 'warehouse near me'",
    "Cake shop": "the festive-order window is short - orders lost to a busy phone line don't come back",
    "North Indian restaurant": "a party that can't book a table online books the restaurant that can - and weekend tables are the margin",
    "Security guard service": "corporate buyers expect an instant quote form - a phone-only enquiry reads as a small operator",
    "Shipping service": "shippers compare quotes at 2am - a phone-only broker doesn't make that shortlist",
    "Pest control service": "someone with a termite problem calls three companies - whoever answers first, wins",
    "Moving service": "people compare 3-4 mover estimates; without a clean quote form you're out before the comparison starts",
    "Massage spa": "a booking that requires a phone call gets abandoned - and no-shows are never recovered",
    "Fitness center": "the trial-seeker clicking your competitor's signup form is your lost membership",
    "Tailor": "alterations clients only remember you when they walk past - no reminder, no return",
    "Repair service": "an urgent repair that hits voicemail goes to the next technician online",
    "Real estate agency": "a buyer enquiry left in chats for a day is a deal closed by the agent who followed up in an hour",
    "Hair salon": "no-shows are never recovered and walk-ins can't see availability",
    "Dry cleaner": "pickup orders still on a WhatsApp thread means lost orders and no reminders",
    "Day spa": "a booking that requires a phone call gets abandoned during the day",
    "Laundry service": "a laundry order that can't be scheduled online goes to the pickup service that can",
    "Laundry": "a laundry order that can't be scheduled online goes to the pickup service that can",
    "Car detailing service": "detailing appointments are lost to long waits and the guy who can book - and nobody repeats",
    "Doctor": "a patient who can't book tonight books the clinic that can",
}

GENERIC_TENSION = "every enquiry not answered quickly goes to whoever answers first online - and repeat customers only remember you when they happen to pass by"

# ---------------------------------------------------------------------------
# SOLUTION: the deliverable for their category.
# ---------------------------------------------------------------------------
CAT_SOLUTION = {
    "Interior designer": "portfolio site + enquiry funnel with automated reply",
    "Dental clinic": "booking + reminder + Google reviews engine",
    "Dentist": "appointment booking + reminder + Google reviews",
    "Transportation service": "quote-request form + WhatsApp reply",
    "Beauty Parlour": "booking page + Instagram-linked booking + review push",
    "Gym": "signup + trial-booking funnel + payment link",
    "Bakery and Cake Shop": "order form + WhatsApp catalog + online payment",
    "Coaching Center": "admission-enquiry funnel + batch listing + demo booking",
    "Education center": "admission funnel + batch info + demo booking",
    "Appliance repair service": "instant booking + job-status tracking + AMC capture",
    "Cafe": "order/booking site + Google visibility + loyalty QR",
    "Boutique": "catalog + trial-appointment booking + payment",
    "Spa": "slot booking + package pricing + review engine",
    "Courier service": "rate calculator + pickup-booking form",
    "Car wash": "slot booking + subscription pack + feedback loop",
    "Hairdresser": "booking + reminder + before/after gallery",
    "Clothing store": "store-front site + WhatsApp catalog + delivery option",
    "Air conditioning repair service": "booking + service-tracking + AMC capture",
    "Warehouse": "capacity enquiry form + postcode-based search",
    "Cake shop": "pre-order form + occasion calendar + online payment",
    "North Indian restaurant": "table booking + online order + Google listing fix",
    "Security guard service": "quote form + compliance/credibility page",
    "Shipping service": "online quote + tracking lookup",
    "Pest control service": "quick-quote + booking + AMC capture",
    "Moving service": "estimate form + transparent pricing page",
    "Massage spa": "slot booking + package page + review push",
    "Fitness center": "signup + trial funnel + payments",
    "Tailor": "custom-order form + measurement guide",
    "Repair service": "booking + tracking + AMC capture",
    "Real estate agency": "property listing site + lead capture + auto-followup",
    "Hair salon": "booking + reminder + before/after gallery",
    "Dry cleaner": "pickup-order + schedule + loyalty",
    "Day spa": "slot booking + packages page",
    "Laundry service": "pickup-order form + schedule + payment",
    "Laundry": "pickup-order + schedule + payment",
    "Car detailing service": "slot booking + package page + before/after proof",
    "Doctor": "appointment booking + reminder + reviews",
}

GENERIC_SOLUTION = "simple website/booking flow + Google visibility + review engine"


# ---------------------------------------------------------------------------
# The frame
# ---------------------------------------------------------------------------
def get(cat):
    cat = (cat or "").strip()
    return {
        "problem": CAT_PROBLEM.get(cat, GENERIC_PROBLEM),
        "tension": CAT_TENSION.get(cat, GENERIC_TENSION),
        "solution": CAT_SOLUTION.get(cat, GENERIC_SOLUTION),
    }


def _get(row, k, default=""):
    try:
        v = row.get(k)
    except AttributeError:
        v = row[k]
    return v if v is not None else default


def frame_lead(row):
    """Row: dict-like (sqlite3.Row or plain dict). Returns {problem, tension,
    solution, project, rating, reviews, area, name, first, cat}."""
    cat = (_get(row, "business_category") or "").strip()
    f = get(cat)
    ex = parse_extras(_get(row, "notes"))

    # PROBLEM prefers scraped reality.
    problem = None
    for col in OBSERVATION_COLS:
        v = (_get(row, col) or "").strip()
        if v and v.lower() not in ("none", "n/a", "-"):
            problem = v.rstrip(".!?")
            break
    problem = problem or f["problem"]

    name = (_get(row, "business_name") or "").split(" | ")[0].strip()
    area = (_get(row, "area") or _get(row, "city") or "Mumbai").strip()

    rating = ex.get("rating")
    reviews = ex.get("reviews_count")

    # PROJECT: estimated deal tier just for framing confidence.
    site = (_get(row, "website_url") or "").strip()
    if not site and not (ex.get("website_status") in ("live",)):
        project = "new build"
    else:
        project = "build / refresh"
    if rating:
        project = f"premium {project}" if float(rating) >= 4.6 else project

    try:
        first = name.split()[0]
    except Exception:
        first = name or "there"

    return {
        "name": name,
        "first": first,
        "cat": cat,
        "area": area,
        "problem": problem,
        "tension": f["tension"],
        "solution": f["solution"],
        "rating": rating,
        "reviews": reviews,
        "project": project,
        "offer_angle": _get(row, "offer_angle") or f["solution"],
    }