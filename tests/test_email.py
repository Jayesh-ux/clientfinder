import sqlite3


def test_accounts_and_draft_lifecycle(init_db_connected, db_path):
    from service_catalog.email import (
        create_account, set_send_enabled, create_draft, list_drafts,
        approve_draft, send_draft,
    )

    acct = create_account({
        "name": "Test Sender",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "sender@example.com",
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "imap_user": "sender@example.com",
        "from_name": "CLIENTFINDER",
        "from_email": "sender@example.com",
    })
    assert acct["send_enabled"] is False

    draft = create_draft({
        "subject": "Hello",
        "body": "This is a draft.",
        "account_id": acct["id"],
    })
    created = list_drafts(status="draft")
    assert any(d["id"] == draft["id"] for d in created)

    # sending without approval must refuse (human-in-the-loop guard)
    res = send_draft(draft["id"])
    assert res["sent"] is False
    assert "approve" in res["error"]

    assert approve_draft(draft["id"]) is True

    # approval alone still refuses when the account is not send-enabled
    res = send_draft(draft["id"])
    assert res["sent"] is False
    assert "send not enabled" in res["error"]

    assert set_send_enabled(acct["id"], True) is True

    # now it fails only because there is no real SMTP server / lead email
    conn = sqlite3.connect(str(db_path))
    has_lead = conn.execute("SELECT count(*) FROM sqlite_master WHERE name='leads'").fetchone()[0]
    conn.close()
    if has_lead:
        res = send_draft(draft["id"])  # no public_business_email -> structured refusal
        assert res["sent"] is False
        assert res["error"] in ("no public email on the linked lead",
                                "draft must be approved first",
                                "account send not enabled")
    else:
        res = send_draft(draft["id"])
        assert res["sent"] is False


def test_inbox_empty_without_network(init_db_connected, db_path):
    from service_catalog.email import create_account, fetch_inbox, list_inbox
    acct = create_account({
        "name": "No Network",
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "imap_user": "u@example.com",
    })
    # No CF_IMAP_PASSWORD secret -> structured refusal, no network touched.
    res = fetch_inbox(acct["id"])
    assert res["error"] is not None
    assert "refusing" in res["error"] or "password" in res["error"].lower()
    assert list_inbox() == []


def test_email_tables_created(init_db_connected, db_path):
    conn = sqlite3.connect(str(db_path))
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert {"email_accounts", "email_drafts", "email_messages"}.issubset(tables)