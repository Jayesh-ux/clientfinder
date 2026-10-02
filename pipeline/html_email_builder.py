"""CLIENTFINDER - build a rich HTML body for an outreach/follow-up draft.

Turns a framed lead (client_framing.frame_lead) + plain text body + subject
into a ready-to-store html_body string, rendered from templates/outreach-email.html
using the ported {{TOKEN}} engine (html_email_render).

Nothing here sends anything - it only renders copy. Drafts stay drafts.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

PIPE = Path(__file__).resolve().parent if "__file__" in locals() else Path(r"C:\Users\hsing\clientfinder-v3\pipeline")
ROOT = PIPE.parent
sys.path.insert(0, str(ROOT))

from html_email_render import render_strict, build_contact_line, escape_html  # noqa: E402

TEMPLATE_PATH = ROOT / "templates" / "outreach-email.html"

SIGNATURE_NAME = "Jayesh Singh"
SIGNATURE_ROLE = "Full-stack developer | booking & enquiry systems for local businesses"

# One contact strip, rendered once per message (high-entropy but consistent).
CONTACT_ITEMS = [
    ("email", "hsinghjayesh@gmail.com"),
    ("phone", "+91 78218 16193"),
    ("url", "hire2onboard.com"),
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


def build_html_body(f, subject, body, business_email=""):
    """f: dict from client_framing.frame_lead; body: plain-text draft body.

    Returns the full HTML <html>...</html> string (storage-ready).
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    greeting = "Hi %s," % (f["first"] or "there")
    opening = _plain_first_para(body)

    problem = (f.get("problem") or f["problem"]).rstrip(".!?") + "."
    tension = (f.get("tension") or f["tension"]).rstrip(".") + "."
    solution = (f["solution"] or "").strip().rstrip(".")
    if solution.lower().startswith(("a ", "an ", "the ")):
        solution = re.sub(r"^(a|an|the)\s+", "", solution, flags=re.I)
    solution = f"{solution} - I can build you a working sample in two days, and you keep it only if it's useful to you."

    # CTA mirrors the plain body's last line if it looks like an ask.
    cta = "Worth a 10-minute call this week?"
    tail = [l for l in (body or "").split("\n") if l.strip()]
    if tail:
        last = tail[-1]
        if "10-minute call" in last or "sample" in last.lower() or "full-time" in last.lower():
            cta = last.rstrip()

    dateline = datetime.now().strftime("%-d %b %Y") if sys.platform != "win32" else datetime.now().strftime("%#d %b %Y")

    replacements = {
        "SUBJECT": subject,
        "BUSINESS_NAME": f["name"],
        "DATELINE": dateline,
        "GREETING": greeting,
        "OPENING": opening,
        "PROBLEM": problem,
        "TENSION": tension,
        "SOLUTION": solution,
        "CTA": cta,
        "SIGNATURE_NAME": SIGNATURE_NAME,
        "SIGNATURE_ROLE": SIGNATURE_ROLE,
        "CONTACT_LINE": build_contact_line(CONTACT_ITEMS),
        "BUSINESS_EMAIL": business_email or "",
        "OPT_OUT": OPT_OUT,
    }
    return render_strict(template, replacements)