"""CLIENTFINDER - build a rich HTML body for an outreach/follow-up draft.

Turns a framed lead (client_framing.frame_lead) + plain text body + subject
into a ready-to-store html_body string, rendered from templates/outreach-email.html
using the ported {{TOKEN}} engine (html_email_render).

Nothing here sends anything - it only renders copy. Drafts stay drafts.
"""
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

PIPE = Path(__file__).resolve().parent
ROOT = PIPE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PIPE))

from html_email_render import render_strict, build_contact_line, escape_html  # noqa: E402

TEMPLATE_PATH = ROOT / "templates" / "outreach-email.html"

SIGNATURE_NAME = "Jayesh Singh"
SIGNATURE_ROLE = "Full-stack developer | booking & enquiry systems for local businesses"

# One contact strip, rendered once per message (high-entropy but consistent).
CONTACT_ITEMS = [
    ("email", "hsinghjayesh@gmail.com"),
    ("phone", "+91 78218 16193"),
    ("url", "github.com/Jayesh-ux"),
    ("url", "linkedin.com/in/jayesh-dev"),
    ("url", "jayesh-ux.github.io/jayesh-singh"),
]

OPT_OUT = "if this isn't relevant, just reply 'stop' and I won't write again."


def _deck_article(text):
    """'booking + reminder + Google reviews engine' -> same (no leading article)."""
    return text


def _plain_first_para(body):
    """Grab the body's opening line for the HTML greeting-replay (draft parity)."""
    for line in (body or "").split("\n"):
        line = line.strip()
        if line:
            return line
    return ""

def de_article(text):
    return re.sub(r"^(a|an|the)\s+", "", text.strip(), flags=re.I)


def build_html_body(f, subject, body, business_email="", phone=""):
    """f: dict from client_framing.frame_lead; body: plain-text draft body.

    Returns the full HTML <html>...</html> string (storage-ready).
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # frame_lead() resolves this: a real contact name, or "<Business> team".
    # Never derive it from the first word of the business name.
    greeting = (f.get("greeting") or f"Hello {f.get('name') or 'there'},")
    if not greeting.endswith(","):
        greeting += ","
    opening = _plain_first_para(body)

    problem = (f.get("problem") or f["problem"]).rstrip(".!?") + "."
    tension = (f.get("tension") or f["tension"]).rstrip(".") + "."
    solution = (f["solution"] or "").strip().rstrip(".")
    if solution.lower().startswith(("a ", "an ", "the ")):
        solution = re.sub(r"^(a|an|the)\s+", "", solution, flags=re.I)
    solution = f"{solution} - I can build you a working sample in two days, and you keep it only if it's useful to you."

    # CTA: a yes/no question ("Worth a 10-minute call this week?") makes the
    # reader do work - they must compose a reply AND propose a time. These
    # owners live on WhatsApp, so make the conversion one tap and low-friction.
    # Lead with a concrete offer of time, not an open ask.
    biz = f.get("name") or "there"
    cta = (f"Pick a time that suits you, {biz} - reply here, tap WhatsApp, or just call. "
           "I hold two slots a day for this.")
    tail = [l for l in (body or "").split("\n") if l.strip()]
    if tail:
        last = tail[-1]
        if "10-minute call" in last and "Worth" in last:
            # Replaced by the booking block below; don't ask twice.
            cta = f"Pick a time that suits you, {biz} - reply here, tap WhatsApp, or just call."

    # One-tap routes. The owner's WhatsApp is the highest-converting channel
    # in India - far above email reply. Pre-fill the message so they don't have
    # to think about what to say.
    phone_raw = (phone or f.get("phone") or "").strip()
    digits = re.sub(r"\D", "", phone_raw)
    # wa.me requires a full E.164 number with NO leading zero: a scraped
    # "09987406937" must become "919987406937" or the link silently fails to
    # open WhatsApp. A failed tap is a lost meeting.
    if digits.startswith("0"):
        digits = digits[1:]
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    wa_digits = ("91" + digits) if len(digits) in (10, 11) else digits

    # Build the booking block as ONE token. The render engine is single-pass,
    # so nested {{TOKENS}} inside a literal block would survive unexpanded and
    # raise in render_strict. Empty output = block disappears (no dead "#"
    # buttons for leads we only have an email for).
    booking = ""
    if digits and len(wa_digits) == 12:
        wa_text = urllib.parse.quote(
            f"Hi Jayesh - saw your note about a walkthrough for {biz}. Happy to "
            f"look at it. What days suit you this week?")
        wa_href = escape_html(f"https://wa.me/{wa_digits}?text={wa_text}")
        tel_href = escape_html(f"tel:{phone_raw}")
        disp = escape_html(phone_raw)
        booking = (
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            'style="margin:0 0 6px;"><tr>'
            f'<td align="center" bgcolor="#16a34a" style="border-radius:6px;">'
            f'<a href="{wa_href}" target="_blank" style="display:inline-block;'
            'padding:11px 20px;font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            'font-weight:600;color:#ffffff;text-decoration:none;border-radius:6px;">'
            'WhatsApp me a time &#8594;</a></td>'
            '<td width="12"></td>'
            f'<td align="center" style="border:1px solid #2563eb;border-radius:6px;">'
            f'<a href="{tel_href}" target="_blank" style="display:inline-block;'
            'padding:10px 20px;font-family:Helvetica,Arial,sans-serif;font-size:14px;'
            'font-weight:600;color:#2563eb;text-decoration:none;border-radius:6px;">'
            f'Call {disp}</a></td>'
            "</tr></table>"
        )
    elif not digits:
        # Email-only lead: keep the ask answerable in one line instead of
        # offering two buttons that do nothing.
        cta = (f"Reply here with a day that suits you - I'll send two time slots "
               f"for {biz} and we're on a 10-minute call.")

    # Specific beats vague. Give two named windows and a real date so the only
    # decision left is which one - and name the fallback for people who won't.
    now = datetime.now()
    (d1, d2) = now + timedelta(days=2), now + timedelta(days=3)
    if booking:
        availability = (
            f"Usually replies within the hour, {d1:%A} {d1:%-d %b} or "
            f"{d2:%A} {d2:%-d %b} work best. No forms, no calendar link - "
            f"WhatsApp or a call and we're talking."
        )
    else:
        availability = (
            f"Usually replies within the hour, {d1:%A} {d1:%-d %b} or "
            f"{d2:%A} {d2:%-d %b} work best. I can also call you first - "
            f"just say when."
        )

    dateline = now.strftime("%-d %b %Y") if sys.platform != "win32" else now.strftime("%#d %b %Y")

    # Proof mirrors the job-application emails, which always lead with a live
    # URL and a number. Every claim here is either a shipped product the reader
    # can open, or a fact we scraped about their own listing.
    proof = (
        "I've shipped three of these: FairPay (fairpaysolution.com) - a live fintech "
        "SaaS with 700+ clients; Hire2Onboard (hire2onboard.com) - a multi-company "
        "recruitment platform; and GeoTrack, where PostGIS spatial caching cut map "
        "API costs ~40%. Same build quality, smaller scope, two days."
    )
    if f.get("reviews"):
        proof = (f"Your own listing proves the demand - {f['reviews']} reviews. "
                 f"{proof}")

    replacements = {
        "SUBJECT": subject,
        "BUSINESS_NAME": f["name"],
        "DATELINE": dateline,
        "GREETING": greeting,
        "OPENING": opening,
        "PROBLEM": problem,
        "TENSION": tension,
        "SOLUTION": solution,
        "PROOF": proof,
        "CTA": cta,
        "BOOKING": booking,
        "AVAILABILITY": availability,
        "SIGNATURE_NAME": SIGNATURE_NAME,
        "SIGNATURE_ROLE": SIGNATURE_ROLE,
        "CONTACT_LINE": build_contact_line(CONTACT_ITEMS),
        "BUSINESS_EMAIL": business_email or "",
        "OPT_OUT": OPT_OUT,
    }
    return render_strict(template, replacements)