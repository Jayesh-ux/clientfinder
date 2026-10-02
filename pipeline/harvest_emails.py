"""Harvest business emails from scraped-lead websites. Polite, resume-safe,
incremental (writes each found email to the DB immediately)."""
import sqlite3
import re
import time
import random
import urllib.request
import ssl
from pathlib import Path
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = Path(__file__).resolve().parent / "crm.db"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
BAD_EMAIL = re.compile(
    r"example|sentry|wixpress|godaddy|godaddysites|jotform|typeform|squarespace|"
    r"\.png|\.jpg|\.jpeg|\.gif|@2x|email protected|no[-_ ]?reply|noreply|localhost|"
    r"\.test$|\.local$|\.invalid$|@x\.|2x@|trellix|sunrust|domain\.com$|yourdomain|"
    r"\.js$|\.css$"
)
LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
CONTACT_HINTS = ("contact", "about", "enquiry", "reach", "connect")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

MAX_LEADS = 160
PROGRESS = Path(__file__).resolve().parent / "harvest_progress.json"


def norm_url(u):
    u = u.strip()
    if not u.startswith("http"):
        u = "https://" + u
    return u.split("?")[0]


def domain_of(url):
    try:
        from urllib.parse import urlparse
        return (urlparse(url).netloc or "").lower().replace("www.", "")
    except Exception:
        return ""


def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
            if resp.status == 200:
                return resp.read(350 * 1024).decode("utf-8", "replace")
    except Exception:
        return None
    return None


def emails_in(html):
    found = set()
    if html:
        for m in EMAIL_RE.findall(html):
            if not BAD_EMAIL.search(m.lower()):
                found.add(m.lower())
    return found


def pick_contact_links(html, base):
    links = []
    for m in LINK_RE.findall(html or ""):
        low = m.lower()
        if any(h in low for h in CONTACT_HINTS) and "mailto:" not in low and "tel:" not in low and ".google" not in low:
            if m.startswith("/"):
                links.append(urljoin(base, m.lstrip("/")))
            elif m.startswith("http"):
                links.append(m)
    return links[:3]


def harvest(lead):
    name, url, phone = lead["business_name"], lead["website_url"], lead["public_business_phone"]
    base = norm_url(url)
    home = fetch(base)
    all_emails = set(emails_in(home))
    if not all_emails and home:
        for link in pick_contact_links(home, base):
            html = fetch(link)
            if html:
                all_emails |= emails_in(html)
                if all_emails:
                    break
            time.sleep(random.uniform(0.2, 0.6))
    if not all_emails:
        return None
    dom = domain_of(base)
    scored = []
    for e in sorted(all_emails):
        edom = e.split("@")[-1].lower()
        score = 100 if edom == dom else (50 if edom.endswith(dom) else 0)
        scored.append((score, e))
    scored.sort(reverse=True)
    return scored[0][1]


def main():
    c = sqlite3.connect(str(DB))
    c.row_factory = sqlite3.Row
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "select lead_id, business_name, website_url, public_business_phone, public_business_email"
        " from leads where website_url != ''"
        " and (public_business_email is null or public_business_email = '')"
        " and source_type = 'google_maps_scrape'"
    ).fetchall()
    prio = sorted(rows, key=lambda r: (1 if (r["public_business_phone"] or "").strip() else 0, str(r["business_name"])), reverse=True)
    prio = prio[:MAX_LEADS]
    print(f"harvesting up to {len(prio)} leads", flush=True)

    store = 0
    tried = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(harvest, r): r for r in prio}
        for i, fut in enumerate(as_completed(futs), 1):
            r = futs[fut]
            tried += 1
            try:
                res = fut.result()
            except Exception:
                res = None
            if res and res != r["public_business_email"]:
                c.execute("update leads set public_business_email=? where lead_id=?",
                          (res, r["lead_id"]))
                c.commit()
                store += 1
                print(f"[{i}/{len(prio)}] STORE {res}  <- {r['business_name'][:36]}", flush=True)
            else:
                print(f"[{i}/{len(prio)}] -", r["business_name"][:36], flush=True)
    c.close()
    print(f"DONE stored={store} tried={tried}", flush=True)


if __name__ == "__main__":
    main()