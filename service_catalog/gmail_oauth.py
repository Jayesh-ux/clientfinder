"""Gmail API send path (OAuth2) for CLIENTFINDER.

Why this exists alongside the SMTP path in service_catalog.email:
send_draft() needs a Gmail *App Password* (CF_SMTP_PASSWORD). When only OAuth2
refresh credentials are available (GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET /
GMAIL_REFRESH_TOKEN) we can send through the Gmail API instead, which needs no
app password and is the supported path for this scope set.

Contract, mirroring the SMTP path:
- Secrets come from the environment only; never stored in the DB or repo.
- The access token is short-lived (~1h) and minted on demand from the refresh
  token. The expired access token pasted by the operator is deliberately NOT
  used - it is dead on arrival.
- No sending happens in this module. It exposes send_message() and every
  call site must have already checked status='approved' + send_enabled=1.
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

TOKEN_URL = "https://oauth2.googleapis.com/token"
SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/{user}/messages/send"
_TIMEOUT = 30


def _env(name, default=""):
    return (os.environ.get(name) or default).strip()


def _load_dotenv():
    """Read .env into os.environ without overriding already-set values.

    Kept minimal on purpose: KEY=VALUE lines, comments and blanks skipped.
    """
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        return


class GmailAuthError(RuntimeError):
    """Refresh credentials missing or rejected by Google."""


class GmailSendError(RuntimeError):
    """Gmail API refused the send (quota, policy, bad recipient...)."""


def get_access_token():
    """Mint a fresh access token from the refresh token.

    Raises GmailAuthError rather than returning an expired token - a silent
    stale token just produces a 401 that looks like a send failure.
    """
    _load_dotenv()
    cid = _env("GMAIL_CLIENT_ID")
    sec = _env("GMAIL_CLIENT_SECRET")
    refresh = _env("GMAIL_REFRESH_TOKEN")
    if not (cid and sec and refresh):
        raise GmailAuthError(
            "missing GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET / GMAIL_REFRESH_TOKEN")

    body = urllib.parse.urlencode({
        "client_id": cid,
        "client_secret": sec,
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise GmailAuthError(f"refresh failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise GmailAuthError(f"refresh unreachable: {exc.reason}") from exc

    token = payload.get("access_token")
    if not token:
        raise GmailAuthError("refresh returned no access_token")
    return token


def _build_raw(to_addr, subject, from_name, from_email, html_body, plain_body):
    """Assemble an RFC822 message and base64url-encode it for the API."""
    msg = EmailMessage()
    msg["Subject"] = subject or ""
    msg["To"] = to_addr
    msg["From"] = f"{from_name or 'CLIENTFINDER'} <{from_email or ''}>"
    if html_body:
        msg.set_content(plain_body or html_body)
        msg.add_alternative(html_body, subtype="html")
    else:
        msg.set_content(plain_body or "")
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")


def send_message(to_addr, subject, html_body="", plain_body="",
                 from_name="", from_email=""):
    """Send one message via the Gmail API. Returns {'sent': bool, 'error': str|None}.

    Never raises - callers decide what a failure means. Errors are returned as
    strings so a batch runner can keep going past one bad recipient.
    """
    if not to_addr:
        return {"sent": False, "error": "no recipient"}
    try:
        token = get_access_token()
    except GmailAuthError as exc:
        return {"sent": False, "error": str(exc)}

    user = _env("GMAIL_USER", "me")
    raw = _build_raw(to_addr, subject, from_name, from_email, html_body, plain_body)
    body = json.dumps({"raw": raw}).encode()
    req = urllib.request.Request(
        SEND_URL.format(user=user), data=body, method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        return {"sent": False, "error": f"HTTP {exc.code}: {detail}"}
    except urllib.error.URLError as exc:
        return {"sent": False, "error": f"unreachable: {exc.reason}"}

    return {"sent": True, "error": None,
            "message_id": payload.get("id"), "thread_id": payload.get("threadId")}
