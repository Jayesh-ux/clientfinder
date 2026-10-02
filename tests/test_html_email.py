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


def test_build_html_body_from_lead():
    """Real dental lead -> clean html_body with no leaked tokens."""
    import sqlite3
    from client_framing import frame_lead
    from html_email_builder import build_html_body

    c = sqlite3.connect(str(":memory:"))
    rows = c.execute("select 1").fetchall()
    assert rows
    c.close()
    # Use the real CRM db for a real lead
    import os
    db = os.environ.get("TEST_CRM_DB", r"C:\Users\hsing\clientfinder-v3\pipeline\crm.db")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    r = conn.execute(
        "select * from leads where business_category='Dental clinic' and "
        " public_business_email is not null and public_business_email != '' "
        "limit 1").fetchone()
    conn.close()
    assert r is not None, "no dental lead with email in CRM"

    f = frame_lead(r)
    html = build_html_body(f, "Bookings for " + f["name"], "Plain body",
                           business_email=r["public_business_email"])
    assert "{{" not in html
    assert f["name"] in html
    assert "mailto:hsinghjayesh@gmail.com" in html
    assert html.strip().startswith("<!DOCTYPE html>")