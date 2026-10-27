"""Bridge scraped JSON (run_scrape.py output) into the v2 leads CSV import.

Reuses import_leads.import_csv so the v2 schema stays the single source of
truth. Derives observation fields that matching consumes (website presence,
phone presence) and leaves the rest neutral.

Usage (from repo root):
    python pipeline/scrape_to_leads.py pipeline/leads_scraped.json
"""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from import_leads import import_csv  # noqa: E402
from service_catalog.config import RAW_DIR, ensure_data_dirs  # noqa: E402

CSV_NAME = "leads_from_scrape.csv"
DEFAULT_COLUMNS = [
    "lead_id", "business_name", "business_category", "sub_category", "city", "area",
    "pincode", "address_public", "website_url", "instagram_url", "facebook_url",
    "linkedin_company_url", "decision_maker_name", "decision_maker_role",
    "public_business_email", "public_business_phone", "contact_form_url",
    "source_type", "source_url", "source_terms_checked", "extraction_method",
    "date_found", "niche", "lead_score", "priority", "owner_assigned",
    "website_status", "mobile_experience", "page_speed_observation",
    "seo_observation", "conversion_observation", "booking_observation",
    "whatsapp_cta_present", "social_activity_observation", "personalisation_note",
    "recommended_offer", "offer_angle", "estimated_project_value_inr",
    "first_contact_channel", "first_contact_date", "first_contact_message",
    "first_contact_status", "whatsapp_number", "whatsapp_permission_status",
    "whatsapp_opt_in_at", "whatsapp_opt_in_source", "whatsapp_opt_in_proof_url",
    "whatsapp_opt_in_text", "whatsapp_opt_out_at", "whatsapp_opt_out_reason",
    "outreach_stage", "last_contacted_at", "next_action_at", "next_action_type",
    "followup_count", "response_status", "meeting_date", "proposal_sent_at",
    "proposal_value_inr", "deal_stage", "deal_value_inr", "notes",
    "do_not_contact", "do_not_contact_reason",
]


KNOWN_CITIES = {
    "Mumbai", "Navi Mumbai", "Thane", "Pune", "Bengaluru", "Gurgaon", "Delhi",
    "Hyderabad", "Chennai", "Ahmedabad", "Panvel", "Vashi", "Nerul", "Belapur",
    "Kharghar", "Kamothe", "Airoli", "Ghansoli", "Bhiwandi", "Taloja", "Mankoli",
    "Bombay",
}


def parse_city_from_address(address: str) -> str:
    if not address:
        return ""
    if "Navi Mumbai" in address:
        return "Navi Mumbai"
    for part in address.split(", "):
        part = part.strip()
        if part in KNOWN_CITIES:
            return part
    if "Mumbai" in address:
        return "Mumbai"
    if "Thane" in address:
        return "Thane"
    return ""


def stable_lead_id(b: dict) -> str:
    """Deterministic lead id so re-importing a scrape cannot duplicate a lead.

    Place id is Google's own unique key and survives re-scrapes. Phone and then
    name+address are fallbacks for records without one. A random uuid here would
    let the same business in twice, which means two outreach drafts for one
    recipient — exactly the duplicate-email failure we must never ship.
    """
    place_id = (b.get("place_id") or "").strip()
    if place_id:
        return "gm_" + hashlib.sha1(place_id.encode("utf-8")).hexdigest()[:16]
    phone = re.sub(r"\D", "", b.get("phone") or "")
    # The same number gets written many ways across scrape sources (+91 X, 0X,
    # X with spaces). Normalise to the bare 10-digit NSN so all forms collide
    # onto one lead instead of becoming repeat outreach targets.
    if phone.startswith("91") and len(phone) == 12:
        phone = phone[2:]
    phone = phone.lstrip("0")
    if phone:
        return "gm_p" + hashlib.sha1(phone.encode("utf-8")).hexdigest()[:16]
    seed = f"{(b.get('name') or '').strip().lower()}|{(b.get('address') or '').strip().lower()}"
    return "gm_n" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def to_row(b: dict) -> dict:
    website = (b.get("website") or "").strip()
    phone = (b.get("phone") or "").strip()
    address = (b.get("address") or "").strip()
    city = (b.get("city") or "").strip() or parse_city_from_address(address)
    name = (b.get("name") or "").strip()

    extra = {}
    for key in ("place_id", "coordinates", "categories", "rating", "reviews_count",
                "reviews_url", "hours", "thumbnail", "link"):
        val = b.get(key)
        if val:
            extra[key] = val

    notes = "auto-imported from run_scrape.py"
    if extra:
        notes += "; " + json.dumps(extra, ensure_ascii=False)

    return {
        "lead_id": stable_lead_id(b),
        "business_name": name,
        "business_category": (b.get("category") or "").strip(),
        "city": city,
        "address_public": address,
        "website_url": website,
        "public_business_phone": phone,
        "source_type": "google_maps_scrape",
        "source_terms_checked": "True",
        "extraction_method": "automated_scrape",
        "website_status": "live" if website else "none",
        "seo_observation": "no website found" if not website else "website found",
        "notes": notes,
    }


def main():
    ensure_data_dirs()
    args = [a for a in sys.argv[1:] if a != "--"]
    if not args:
        raise SystemExit("Usage: python pipeline/scrape_to_leads.py <scraped.json>")
    src = Path(args[0])
    if not src.is_absolute() and not src.exists():
        fallback = RAW_DIR / src.name
        if fallback.exists():
            src = fallback
    businesses = json.loads(src.read_text(encoding="utf-8"))
    rows = [to_row(b) for b in businesses]

    csv_path = RAW_DIR / CSV_NAME
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows -> {csv_path}")
    import_csv(str(csv_path))


if __name__ == "__main__":
    main()