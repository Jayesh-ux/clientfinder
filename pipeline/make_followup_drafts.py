"""CLIENTFINDER - generate follow-up email DRAFTS for prior-sent leads.

Follow-up logic per docs/client_approach_playbook.md:
  touch 1 = intro (already sent)
  touch 2 = replay  (day +3..+4, new angle + new proof point)
  touch 3 = value-drop (day +7, free insight slice)
  touch 4 = timer    (day +14, time-boxed offer)
  touch 5 = archive  (no reply -> drop to phone/call list)

Only creates DRAFTS. Never sends. Updates lead CRM fields so the sequence
is trackable and resumable.

Usage:
  python make_followup_drafts.py                 # next follow-up for all sent leads
  python make_followup_drafts.py --touch 2       # force touch index (0..3)
"""
import argparse
import random
import sqlite3
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

PIPE = Path(__file__).resolve().parent if "__file__" in locals() else Path(r"C:\Users\hsing\clientfinder-v3\pipeline")
ROOT = PIPE.parent
sys.path.insert(0, str(ROOT))

from service_catalog.email import create_draft, list_accounts  # noqa: E402
from client_framing import frame_lead  # noqa: E402
from html_email_builder import build_html_body  # noqa: E402

SIGN = ("Jayesh Singh\n+91 78218 16193 | hsinghjayesh@gmail.com\n"
        "github.com/Jayesh-ux | linkedin.com/in/jayesh-dev | jayesh-ux.github.io/jayesh-singh")
ACC_ID = next(a["id"] for a in list_accounts() if a["from_email"] == "hsinghjayesh@gmail.com")

TOUCH_LABEL = ["followup-1", "followup-2", "followup-3", "followup-4"]
TOUCH_PREFIX = ["Re:", "Re:", "Re:", "Last one -"]

# Each touch has 2-3 high-entropy variants; pick one at random (anti-fingerprint).

T2_BODIES = [
    "{first}, circling back on {name}. You get calls all day - I get it, owners do. "
    "But that's exactly the point: a {solution} exists so the calls that matter stop "
    "depending on whoever picks up. {proof} Free 2-day sample still stands - I'll "
    "have it live before you decide anything.",
    "Hi {first}. Not chasing - just making this easier on you. Between running "
    "{name} you shouldn't have to answer 'is there a slot?' ten times a day. "
    "A {solution} fixes exactly that. {proof} Worth a 10-minute look this week? "
    "The sample build costs you nothing.",
    "Hi {first}, following up on my earlier message. {name} has the reputation "
    "({rating}, {reviews} reviews) but none of it converts while enquiries come "
    "in by phone. A {solution} changes that - {proof} A 10-minute call, no "
    "commitment - worst case you get a free look at how your customers find you.",
]

T3_BODIES = [
    "{first} - no pitch today, just a useful 2 minutes for {name}. I pulled your "
    "Google presence while building my sample. Three things I found:\n"
    "1. {obs1}\n2. {obs2}\n3. {obs3}\n\n"
    "That middle one is quietly costing {name} someone every week, and it's a "
    "15-minute fix once you see it. Happy to show you - no strings. And yes, "
    "still open to a full-time dev role if that fits you better.",
    "Hi {first}. Instead of another pitch, here's a free slice of what I do for "
    "businesses like {name}: most owners never see the gaps I found for you - "
    "{obs1}, {obs2}, {obs3}. Fixing just the first one is a one-day build. "
    "Want me to show you live? Also open to full-time work if that suits you "
    "better.",
]

T4_BODIES = [
    "{first}, closing the loop on {name}. I'm building two more sample systems "
    "this month before I focus on projects, and I'd rather it be for a business "
    "with your reputation. If you want {solution}, reply by {deadline} and I'll "
    "slot you in. If it's a no, no hard feelings - and my full-time search "
    "continues either way.",
    "Last note from me, {first}. If {name} ever wants enquiries that answer "
    "themselves and bookings that show up, the door's open - {solution}. "
    "I'll leave the offer standing till {deadline}. Apologies for the multiple "
    "notes; that's the last one. (And if full-time roles interest you, I'm "
    "around.)",
]


def render(tmpl, **kw):
    return textwrap.dedent(tmpl).strip().format(**kw)


def build_body(touch, f):
    name = f["name"]
    first = f["first"]
    rating = f"{f['rating']}" if f["rating"] else "top"
    reviews = f"{f['reviews']}" if f["reviews"] else "strong"

    solution = f["solution"]
    if solution.lower().startswith(("a ", "an ", "the ")):
        solution = solution.split(" ", 1)[1]

    # NEW proof point anchored to the frame, different on every touch.
    site = f.get("website_status")
    if f["project"] == "new build":
        proof = f"Right now {name} isn't reachable from a local Google search - the enquiry window is fully offline."
    else:
        proof = f"{name} ranks on reviews but the funnel stops at a phone number."
    deadline = (datetime.now() + timedelta(days=5)).strftime("%d %b")

    if touch == 0:
        body = render(random.choice(T2_BODIES),
                      first=first, name=name, solution=solution,
                      proof=proof, rating=rating, reviews=reviews)
    elif touch == 1:
        obs = [o for o in (f.get("obs1"), f.get("obs2"), f.get("obs3")) if o] or [
            "enquiries can't be booked online", "no reminder goes out", "no lead is ever logged"]
        body = render(random.choice(T3_BODIES),
                      first=first, name=name, obs1=obs[0], obs2=obs[1], obs3=obs[2])
    else:
        body = render(random.choice(T4_BODIES),
                      first=first, name=name, solution=solution, deadline=deadline)

    cta = "\n\nWorth a 10-minute call this week?" if not body.rstrip().endswith("?") else ""
    return body + cta + "\n\n" + SIGN


def current_touch(c, lead_id):
    r = c.execute("select count(*) n from email_drafts where lead_id=? and status='sent'", (lead_id,)).fetchone()
    return max(0, (r["n"] - 1) if r else 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--touch", type=int, default=None, help="force touch index 0..3")
    ap.add_argument("--no-update-crm", action="store_true")
    args = ap.parse_args()

    c = sqlite3.connect(str(PIPE / "crm.db"), timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")

    # leads that have at least one SENT outreach email and are still alive
    leads = c.execute(
        "select l.*, "
        " (select d.subject from email_drafts d where d.lead_id = l.lead_id and d.status='sent'"
        "  order by d.created_at desc limit 1) as last_sent_subject"
        " from leads l"
        " where exists (select 1 from email_drafts d where d.lead_id = l.lead_id and d.status='sent')"
        "   and (l.do_not_contact is null or l.do_not_contact = 0)"
    ).fetchall()

    made = skipped = 0
    now = datetime.now()
    for r in leads:
        f = frame_lead(r)
        if not f["name"] or not f["first"]:
            skipped += 1
            continue

        # align observation text for value-drop touch
        f["obs1"] = f["problem"].lower()
        f["obs2"] = "no automatic follow-up goes out after an enquiry"
        f["obs3"] = f"phone-only means nothing you sell is bookable without staff time"
        f["website_status"] = r["website_status"] if "website_status" in r.keys() else None

        t = args.touch if args.touch is not None else current_touch(c, r["lead_id"])
        if t > 3:
            # already at max follow-ups -> next step is call channel
            c.execute("update leads set outreach_stage='call-target', next_action_type='phone' where lead_id=?",
                      (r["lead_id"],))
            skipped += 1
            continue

        subject = f"{TOUCH_PREFIX[t]} {r['last_sent_subject']}".strip()
        body = build_body(t, f)
        html_body = build_html_body(f, subject, body, business_email=r["public_business_email"] or "")

        d = create_draft({
            "lead_id": r["lead_id"],
            "solution_slug": f["offer_angle"],
            "account_id": ACC_ID,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "tags": "client-outreach,%s,html" % TOUCH_LABEL[t],
        })

        if not args.no_update_crm:
            c.execute(
                "update leads set outreach_stage=?, followup_count=?,"
                " next_action_type='followup-email', next_action_at=?, last_contacted_at=? where lead_id=?",
                (TOUCH_LABEL[t], t + 1, (now + timedelta(days=3)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M"), r["lead_id"]),
            )
            c.commit()  # release write lock so create_draft's own connection can write
        made += 1
        print(f"draft {d['id']} touch={t+1} | {subject}")

    c.commit()
    c.close()
    print(f"\ncreated {made} follow-up drafts, skipped {skipped}")


if __name__ == "__main__":
    main()