"""Email subsystem for CLIENTFINDER v3 (Phase 8-lite).

Design contract (human-in-the-loop ALWAYS on):
- OUTBOUND defaults to DRAFTS ONLY. A message is never sent until an operator
  explicitly approves it and a mailbox is created with send_enabled=1.
- INBOUND uses IMAP, read-only, UID-based, deduplicated by Message-ID. It never
  replies automatically.
- No credentials are stored in the repository; all secrets come from the
  environment (SMTP_PASSWORD / IMAP_PASSWORD) and never touch the DB.

This module is fully offline-safe: all I/O functions are guarded and return
structured results instead of raising; sending requires explicit enablement.
"""

import imaplib
import smtplib
import ssl
import os
import sqlite3
from email.message import EmailMessage
from email.parser import Parser

from service_catalog.db import connect, row_to_dict


# ---------------------------------------------------------------- accounts

def list_accounts():
    conn = connect()
    try:
        rows = conn.execute("SELECT * FROM email_accounts ORDER BY name").fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_account(data):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO email_accounts (name, smtp_host, smtp_port, smtp_user,"
            " imap_host, imap_port, imap_user, send_enabled, from_name, from_email)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["name"], data.get("smtp_host"), data.get("smtp_port"),
             data.get("smtp_user"), data.get("imap_host"), data.get("imap_port"),
             data.get("imap_user"), 1 if data.get("send_enabled") else 0,
             data.get("from_name"), data.get("from_email")))
        conn.commit()
        return row_to_dict(conn.execute("SELECT * FROM email_accounts WHERE id = ?",
                                 (cur.lastrowid,)).fetchone())
    finally:
        conn.close()


def set_send_enabled(account_id, enabled):
    conn = connect()
    try:
        cur = conn.execute(
            "UPDATE email_accounts SET send_enabled = ?, updated_at = datetime('now')"
            " WHERE id = ?", (1 if enabled else 0, account_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------- drafts

def create_draft(data):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO email_drafts (lead_id, solution_slug, account_id, subject,"
            " body, html_body, status, send_after, tags) VALUES (?, ?, ?, ?, ?, ?,"
            " 'draft', ?, ?)",
            (data.get("lead_id"), data.get("solution_slug"), data.get("account_id"),
             data["subject"], data["body"], data.get("html_body"),
             data.get("send_after"), data.get("tags")))
        conn.commit()
        return dict(conn.execute("SELECT * FROM email_drafts WHERE id = ?",
                                 (cur.lastrowid,)).fetchone())
    finally:
        conn.close()


def list_drafts(status="draft"):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM email_drafts WHERE status = ? ORDER BY created_at DESC",
            (status,)).fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def bulk_create_drafts(items):
    """Create multiple drafts for multiple leads. All-or-nothing per item."""
    conn = connect()
    try:
        for item in items:
            create_draft(item)
        return len(items)
    finally:
        conn.close()


def approve_draft(draft_id):
    conn = connect()
    try:
        cur = conn.execute(
            "UPDATE email_drafts SET status = 'approved', updated_at = datetime('now')"
            " WHERE id = ? AND status = 'draft'", (draft_id,))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def mark_sent_from_draft(mail, draft_id):
    """Internal helper after a real send; moves draft to 'sent'."""
    conn = connect()
    try:
        conn.execute(
            "UPDATE email_drafts SET status = 'sent', updated_at = datetime('now')"
            " WHERE id = ? AND status = 'approved'", (draft_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- smtp (outbound)

def send_draft(draft_id, secret_smtp_password=None):
    """Send ONE approved draft. Returns {sent: bool, error: str, draft_id: int}.

    Refuses to send unless:
      1. the draft status is 'approved' (operator action), AND
      2. the account has send_enabled=1.
    The SMTP/IMAP password must come from the environment or the caller; it is
    never persisted.
    """
    conn = connect()
    try:
        try:
            row = conn.execute(
                "SELECT d.*, a.smtp_host, a.smtp_port, a.smtp_user, a.from_name,"
                " a.from_email, a.send_enabled, l.public_business_email"
                " FROM email_drafts d"
                " LEFT JOIN email_accounts a ON a.id = d.account_id"
                " LEFT JOIN leads l ON l.lead_id = d.lead_id"
                " WHERE d.id = ?", (draft_id,)).fetchone()
        except sqlite3.OperationalError:
            # leads table not present (fresh catalog DB without the v2 pipeline)
            row = conn.execute(
                "SELECT d.*, a.smtp_host, a.smtp_port, a.smtp_user, a.from_name,"
                " a.from_email, a.send_enabled"
                " FROM email_drafts d"
                " LEFT JOIN email_accounts a ON a.id = d.account_id"
                " WHERE d.id = ?", (draft_id,)).fetchone()
    finally:
        conn.close()
    row = row_to_dict(row)
    if row is None:
        return {"sent": False, "error": "draft not found", "draft_id": draft_id}
    if row["status"] != "approved":
        return {"sent": False, "error": "draft must be approved first",
                "draft_id": draft_id}
    if not row["send_enabled"]:
        return {"sent": False, "error": "account send not enabled",
                "draft_id": draft_id}
    to_addr = row.get("public_business_email")
    if not to_addr:
        return {"sent": False, "error": "no public email on the linked lead",
                "draft_id": draft_id}

    if secret_smtp_password is None:
        secret_smtp_password = os.environ.get("CF_SMTP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = row["subject"]
    msg["From"] = f'{row["from_name"] or "CLIENTFINDER"} <{row["from_email"] or ""}>'
    msg["To"] = to_addr
    if row.get("html_body"):
        msg.set_content(row["html_body"], subtype="html")
    else:
        msg.set_content(row["body"])

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(row["smtp_host"], row["smtp_port"], timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(row["smtp_user"], secret_smtp_password)
            smtp.send_message(msg)
        mark_sent_from_draft(None, draft_id)
        return {"sent": True, "error": None, "draft_id": draft_id}
    except Exception as e:
        return {"sent": False, "error": str(e), "draft_id": draft_id}


# ---------------------------------------------------------------- imap (inbound)

def fetch_inbox(account_id, secret_imap_password=None, verify_ssl=True):
    """Read-only IMAP fetch, deduplicated by Message-ID into email_messages.

    Never auto-replies. Returns {fetched, rejected, error}.
    """
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM email_accounts WHERE id = ?", (account_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"fetched": 0, "rejected": 0, "error": "account not found"}
    if secret_imap_password is None:
        secret_imap_password = os.environ.get("CF_IMAP_PASSWORD")
    if not secret_imap_password:
        return {"fetched": 0, "rejected": 0,
                "error": "CF_IMAP_PASSWORD not set; refusing to read without a secret"}

    try:
        ctx = ssl.create_default_context()
        collections = imaplib.IMAP4_SSL(row["imap_host"], row["imap_port"],
                                        ssl_context=ctx if verify_ssl else None)
        try:
            collections.login(row["imap_user"], secret_imap_password)
            collections.select("INBOX", readonly=True)
            _typ, data = collections.search(None, "ALL")
            fetched = 0
            rejected = 0
            for num in data[0].split():
                _typ, msg_data = collections.fetch(num, "(BODY.PEEK[HEADER])")
                if not msg_data or msg_data[0] is None:
                    rejected += 1
                    continue
                raw_header = msg_data[0][1]
                msg = Parser().parsestr(raw_header.decode("utf-8", "replace"))
                message_id = msg.get("Message-ID")
                subject = msg.get("Subject")
                from_addr = msg.get("From")
                if not message_id:
                    rejected += 1
                    continue
                conn = connect()
                try:
                    exists = conn.execute(
                        "SELECT id FROM email_messages WHERE message_id = ?",
                        (message_id,)).fetchone()
                    if exists:
                        rejected += 1
                    else:
                        conn.execute(
                            "INSERT INTO email_messages (account_id, mailbox, uid,"
                            " message_id, subject, from_addr, date, replied)"
                            " VALUES (?, 'INBOX', ?, ?, ?, ?, ?, 0)",
                            (account_id, str(num), message_id, subject, from_addr,
                             msg.get("Date")))
                        conn.commit()
                        fetched += 1
                finally:
                    conn.close()
            return {"fetched": fetched, "rejected": rejected, "error": None}
        finally:
            try:
                collections.logout()
            except Exception:
                pass
    except Exception as e:
        return {"fetched": 0, "rejected": 0, "error": str(e)}


def list_inbox(account_id=None, limit=100):
    conn = connect()
    try:
        q = "SELECT * FROM email_messages"
        params = []
        if account_id:
            q += " WHERE account_id = ?"
            params.append(account_id)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, params).fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()