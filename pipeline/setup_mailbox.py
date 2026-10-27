"""Register (or update) the outreach mailbox used by the draft generators.

make_outreach_drafts.py / make_followup_drafts.py pick their account by
from_email. Without a row in `email_accounts` those scripts abort with a
StopIteration, so this is the one setup step that must not be manual.

Passwords are never stored here - SMTP/IMAP secrets are read from the
environment (CF_SMTP_PASSWORD / CF_IMAP_PASSWORD, see .env.example).

Usage:
    python pipeline/setup_mailbox.py --email you@gmail.com --name "Your Name"
    python pipeline/setup_mailbox.py --email you@gmail.com --disable-send
    python pipeline/setup_mailbox.py --list
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service_catalog.email import create_account, list_accounts, set_send_enabled  # noqa: E402


def upsert(email, name, send_enabled, host="smtp.gmail.com", imap_host="imap.gmail.com"):
    for account in list_accounts():
        if (account.get("from_email") or "").lower() == email.lower():
            set_send_enabled(account["id"], send_enabled)
            return account["id"], "updated"
    account = create_account({
        "name": name or email,
        "smtp_host": host,
        "smtp_port": 587,
        "smtp_user": email,
        "imap_host": imap_host,
        "imap_port": 993,
        "imap_user": email,
        "send_enabled": send_enabled,
        "from_name": name or None,
        "from_email": email,
    })
    return account["id"], "created"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--email", help="Gmail address used as the From address")
    ap.add_argument("--name", default="", help="Display name for the From header")
    ap.add_argument("--disable-send", action="store_true",
                    help="register the mailbox with send_enabled=0 (drafts only)")
    ap.add_argument("--list", action="store_true", help="list registered mailboxes")
    args = ap.parse_args()

    if args.list or not args.email:
        accounts = list_accounts()
        if not accounts:
            print("no mailboxes registered; run with --email you@gmail.com")
            return 1
        for a in accounts:
            print(f"{a['id']:>3}  {a['from_email'] or '-':<32} "
                  f"send_enabled={bool(a['send_enabled'])}")
        return 0

    send_enabled = not args.disable_send
    account_id, action = upsert(args.email, args.name, send_enabled)
    print(f"{action} mailbox id={account_id} for {args.email} "
          f"(send_enabled={int(send_enabled)})")
    if send_enabled:
        print("Reminder: sending also needs CF_SMTP_PASSWORD in .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main())