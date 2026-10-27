import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))


def test_sanitize_url_allowlist():
    from html_email_render import sanitize_url, as_url
    assert sanitize_url("mailto:x@y.com") == "mailto:x@y.com"
    assert sanitize_url("x@y.com") == "mailto:x@y.com"
    assert sanitize_url("javascript:alert(1)") == ""
    assert sanitize_url("https://ok.com") == "https://ok.com"
    assert sanitize_url("github.com/Jayesh-ux") == "https://github.com/Jayesh-ux"
    assert as_url("github.com/Jayesh-ux") == "https://github.com/Jayesh-ux"


def test_escape_at_leaf():
    from html_email_render import escape_html
    assert escape_html("<b>&") == "&lt;b&gt;&amp;"
    assert escape_html(None) == ""


def test_single_pass_substitution_no_reinterpretation():
    from html_email_render import render
    out = render("{{A}} {{B}}", {"A": "ok", "B": "{{A}}"})
    assert out == "ok {{A}}"


def test_strict_raises_on_unresolved():
    from html_email_render import render_strict
    with pytest.raises(ValueError, match="MISSING"):
        render_strict("{{A}} {{MISSING}}", {"A": "x"})


SYNTHETIC_LEAD = {
    "lead_id": "test-dental-1",
    "business_name": "Sunrise Dental Clinic",
    "business_category": "Dental clinic",
    "area": "Andheri",
    "city": "Mumbai",
    "website_url": "",
    "booking_observation": "No online booking available; phone only",
    "conversion_observation": "",
    "social_activity_observation": "",
    "notes": "auto-imported from run_scrape.py; {\"rating\": 4.3, \"reviews_count\": 87}",
    "public_business_email": "hello@sunrisedental.example",
}


def _dental_lead_row():
    """A dental lead with a public email, from the real CRM when available."""
    import sqlite3

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from service_catalog.config import get_test_db_path

    db = get_test_db_path()
    if Path(db).is_file():
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        has_leads = conn.execute(
            "select 1 from sqlite_master where type='table' and name='leads'"
        ).fetchone() is not None
        row = None
        if has_leads:
            row = conn.execute(
                "select * from leads where business_category='Dental clinic' and "
                " public_business_email is not null and public_business_email != '' "
                "limit 1").fetchone()
        conn.close()
        if row is not None:
            return row
    return SYNTHETIC_LEAD


def test_build_html_body_from_lead():
    """Dental lead -> clean html_body with no leaked tokens."""
    from client_framing import frame_lead
    from html_email_builder import build_html_body

    r = _dental_lead_row()
    f = frame_lead(r)
    html = build_html_body(f, "Bookings for " + f["name"], "Plain body",
                           business_email=r["public_business_email"])
    assert "{{" not in html
    assert f["name"] in html
    assert "mailto:hsinghjayesh@gmail.com" in html
    assert html.strip().startswith("<!DOCTYPE html>")

def test_wa_link_drops_leading_zero_for_e164():
    """A scraped '09987406937' must become 919987406937.

    wa.me rejects any number that isn't E.164, so the leading zero silently
    produced a WhatsApp link that opens nothing - a lost meeting.
    """
    from html_email_builder import build_html_body
    from client_framing import frame_lead

    f = frame_lead({"business_name": "Harsha & Rakesh Salon", "business_category": "Salon",
                    "area": "Mumbai", "notes": "", "decision_maker_name": ""})
    html = build_html_body(f, "s", "body", business_email="x@y.com",
                           phone="09987406937")
    import re
    m = re.search(r"href=\"https://wa\.me/(\d+)", html)
    assert m, "whatsapp booking link missing"
    assert m.group(1) == "919987406937"


def test_no_dead_booking_links_when_phone_missing():
    """Email-only leads must not get href='#' buttons - a dead tap loses them."""
    from html_email_builder import build_html_body
    from client_framing import frame_lead

    f = frame_lead({"business_name": "Greenfield Interior Studio",
                    "business_category": "Interior designer", "area": "Mumbai",
                    "notes": "", "decision_maker_name": ""})
    html = build_html_body(f, "s", "body", business_email="a@b.in", phone="")
    assert 'wa.me' not in html
    assert 'href="#"' not in html
    assert "WhatsApp me a time" not in html
    assert "Reply here with a day" in html  # ask stays answerable in one line


def test_booking_block_has_no_unrendered_tokens():
    from html_email_builder import build_html_body
    from client_framing import frame_lead

    f = frame_lead({"business_name": "I 10 Day Spa", "business_category": "Spa",
                    "area": "Mumbai", "notes": "", "decision_maker_name": ""})
    html = build_html_body(f, "s", "body", business_email="a@b.in",
                           phone="+91 98203 29444")
    assert "{{" not in html  # render_strict would raise; pin it anyway
    assert "wa.me/919820329444" in html
    assert "tel:+91 98203 29444" in html
