"""Bridge scraped JSON (run_scrape.py output) into the v2 leads CSV import.

Reuses import_leads.import_csv so the v2 schema stays the single source of
truth. Derives observation fields that matching consumes (website presence,
phone presence) and leaves the rest neutral.

Usage (from repo root):
    python pipeline/scrape_to_leads.py pipeline/leads_scraped.json
"""

import csv
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_leads import import_csv  # noqa: E402

CSV_PATH = "pipeline/leads_from_scrape.csv"
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
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python pipeline/scrape_to_leads.py <scraped.json>")
    src = Path(sys.argv[1])
    businesses = json.loads(src.read_text(encoding="utf-8"))
    rows = [to_row(b) for b in businesses]

    csv_path = Path(__file__).resolve().parent.parent / CSV_PATH
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows -> {csv_path}")
    import_csv(str(csv_path))


if __name__ == "__main__":
    main()