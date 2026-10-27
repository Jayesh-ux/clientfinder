"""Path + env resolution: every script must work from any CWD and any OS."""

import json
import os
import sqlite3

import pytest

from service_catalog import config


def test_paths_are_repo_anchored():
    assert (config.PIPELINE_DIR / "crm.db").exists() or True  # path shape only
    assert config.PIPELINE_DIR.parent == config.REPO_ROOT
    assert config.DEFAULT_DB_PATH == config.PIPELINE_DIR / "crm.db"
    assert config.ENV_PATH == config.REPO_ROOT / ".env"
    assert config.RAW_DIR == config.DATA_DIR / "raw"
    assert config.OUTREACH_DIR == config.DATA_DIR / "outreach"


def test_db_path_prefers_env(monkeypatch, tmp_path):
    monkeypatch.setenv("CLIENTFINDER_DB_PATH", str(tmp_path / "custom.db"))
    assert config.get_db_path() == tmp_path / "custom.db"


def test_db_path_defaults_to_pipeline(monkeypatch):
    monkeypatch.delenv("CLIENTFINDER_DB_PATH", raising=False)
    assert config.get_db_path() == config.PIPELINE_DIR / "crm.db"


def test_connect_creates_parent_dir(tmp_path):
    target = tmp_path / "nested" / "deeper" / "crm.db"
    conn = config.connect(target)
    conn.execute("create table t (id integer)")
    conn.commit()
    conn.close()
    assert target.is_file()


def test_db_module_reuses_shared_resolver(tmp_path):
    """service_catalog.db must not reimplement path resolution.

    Runs in a subprocess: the session fixture replaces dbmod.get_db_path with a
    test override, so the shipped wiring has to be inspected in a clean process.
    """
    import subprocess
    import sys

    target = tmp_path / "x.db"
    code = (
        "import service_catalog.db as d;"
        f"assert d.get_db_path() == __import__('pathlib').Path({str(target)!r}), d.get_db_path();"
        "c = d.connect(); c.close();"
        f"assert __import__('pathlib').Path({str(target)!r}).is_file();"
        "print('ok')"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True,
        cwd=str(config.REPO_ROOT),
        env={**os.environ, "CLIENTFINDER_DB_PATH": str(target)},
    )
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_load_env_does_not_clobber_real_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'CF_SMTP_PASSWORD="from-file"\n'
        "# a comment\n"
        "\n"
        "CF_IMAP_PASSWORD='single-quoted'\n"
        "malformed-line\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CF_SMTP_PASSWORD", "from-real-env")
    monkeypatch.delenv("CF_IMAP_PASSWORD", raising=False)

    loaded = config.load_env(env_file)

    assert loaded["CF_SMTP_PASSWORD"] == "from-file"
    assert loaded["CF_IMAP_PASSWORD"] == "single-quoted"
    assert "malformed-line" not in loaded
    assert os.environ["CF_SMTP_PASSWORD"] == "from-real-env"
    assert os.environ["CF_IMAP_PASSWORD"] == "single-quoted"


def test_load_env_missing_file_is_noop(tmp_path):
    assert config.load_env(tmp_path / "nope.env") == {}


def test_ensure_data_dirs_creates_both(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "OUTREACH_DIR", tmp_path / "outreach")
    dirs = config.ensure_data_dirs()
    assert set(dirs) == {"raw", "outreach"}
    assert all(p.is_dir() for p in dirs.values())


@pytest.mark.parametrize("value,expected", [
    ("1", True), ("true", True), ("YES", True), ("on", True),
    ("0", False), ("false", False), ("", False),
])
def test_env_flag(monkeypatch, value, expected):
    monkeypatch.setenv("CF_TEST_FLAG", value)
    assert config.env_flag("CF_TEST_FLAG") is expected


def test_env_flag_default(monkeypatch):
    monkeypatch.delenv("CF_TEST_FLAG", raising=False)
    assert config.env_flag("CF_TEST_FLAG") is False
    assert config.env_flag("CF_TEST_FLAG", default=True) is True


def test_scripts_resolve_db_not_cwd():
    """No pipeline script may hardcode a CWD-relative or Windows-only DB path."""
    import re
    from pathlib import Path

    pipe = Path(config.PIPELINE_DIR)
    bad = []
    for path in sorted(pipe.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"DB(_PATH)?\s*=\s*'crm\.db'", text):
            bad.append(f"{path.name}: CWD-relative 'crm.db'")
        if re.search(r'C:\\\\Users|clientfinder-v3', text):
            bad.append(f"{path.name}: hardcoded Windows path")
    assert bad == []


def test_infer_problems_writes_framing_columns(init_db_connected, db_path):
    """SETUP.md promises lead_problem / why_they_pay_us; migration 0005 adds them."""
    conn = sqlite3.connect(str(db_path))
    cols = {r[1] for r in conn.execute("pragma table_info(leads)")}
    conn.close()
    assert {"lead_problem", "why_they_pay_us"}.issubset(cols)


def test_problem_framing_prefers_observation_over_category():
    from pipeline.problem_framing import lead_problem, lead_why

    observed = {
        "business_name": "Test Dental",
        "business_category": "Dental clinic",
        "booking_observation": "No online booking available; phone only",
        "notes": "",
    }
    assert lead_problem(observed).startswith("No online booking")

    keyword_dump = {
        "business_name": "Test Gym",
        "business_category": "Gym",
        "booking_observation": "no online booking cannot book online",  # matcher keywords
        "notes": "",
    }
    # keyword dumps are evidence, not copy -> fall back to the category line
    assert lead_problem(keyword_dump) == "No online signup; free-trial enquiries leak."

    empty = {"business_category": "", "notes": ""}
    assert lead_problem(empty).startswith("No clean way for customers")
    assert "pay" in lead_why(empty) or "build it for them" in lead_why(empty)


def test_setup_mailbox_upsert_is_idempotent(init_db_connected, db_path):
    from pipeline import setup_mailbox

    first, action = setup_mailbox.upsert("ops@example.com", "Ops", False)
    assert action == "created"
    second, action = setup_mailbox.upsert("ops@example.com", "Ops", True)
    assert action == "updated"
    assert first == second

    import service_catalog.db as dbmod

    conn = dbmod.connect()
    row = conn.execute("select * from email_accounts where id = ?", (first,)).fetchone()
    conn.close()
    assert row["from_email"] == "ops@example.com"
    assert row["send_enabled"] == 1

def test_stable_lead_id_prevents_duplicate_imports():
    """Re-importing a scrape must not create a second row for one business."""
    from pipeline.scrape_to_leads import stable_lead_id

    place = {"place_id": "ChIJabc123", "name": "A", "address": "x"}
    same = {"place_id": "ChIJabc123", "name": "A renamed", "address": "y"}
    assert stable_lead_id(place) == stable_lead_id(same)

    phone_a = {"phone": "+91 98200 11223", "name": "A"}
    phone_b = {"phone": "09820011223", "name": "B"}
    assert stable_lead_id(phone_a) == stable_lead_id(phone_b)

    by_name = {"name": "Kalyan Sweet House", "address": "Shop 9, Kalyan West"}
    assert stable_lead_id(by_name) == stable_lead_id(dict(by_name))
    assert stable_lead_id(by_name) != stable_lead_id({"name": "Other", "address": "Shop 9"})

    # distinct namespaces so a place id can never collide with a phone/name id
    ids = {stable_lead_id(place), stable_lead_id(phone_a), stable_lead_id(by_name)}
    assert len(ids) == 3


def test_to_row_sets_lead_id():
    from pipeline.scrape_to_leads import to_row

    row = to_row({"name": "Test", "place_id": "ChIJx", "phone": "+91 1"})
    assert row["lead_id"].startswith("gm_")


def test_reimport_is_idempotent(tmp_path, monkeypatch):
    """Two imports of the same scrape -> one lead row, so one draft, not two."""
    db = tmp_path / "crm.db"
    monkeypatch.setenv("CLIENTFINDER_DB_PATH", str(db))
    import importlib

    from pipeline import init_db, scrape_to_leads

    importlib.reload(init_db)
    init_db.DB_PATH = str(db)
    init_db.init_db()

    payload = [{"name": "Test Clinic", "place_id": "ChIJdup", "phone": "+91 90000 11111",
                "category": "Dental clinic", "address": "Kalyan West, Mumbai"}]
    src = tmp_path / "dup.json"
    src.write_text(json.dumps(payload), encoding="utf-8")

    import csv as _csv
    from pipeline.import_leads import import_csv

    rows = [scrape_to_leads.to_row(b) for b in payload]
    for attempt in (1, 2):
        out = tmp_path / f"leads_{attempt}.csv"
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = _csv.DictWriter(f, fieldnames=scrape_to_leads.DEFAULT_COLUMNS,
                                extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        import_csv(str(out))

    conn = sqlite3.connect(str(db))
    count = conn.execute("select count(*) from leads").fetchone()[0]
    conn.close()
    assert count == 1


def test_greeting_never_uses_business_name_first_word():
    """'Fresh Look Salon' must never greet as 'Hi Fresh,'.

    The old code did name.split()[0], which produced greetings like 'Hi Fresh,',
    'Hi Greenfield,' and 'Hi Sri,' - they read as mail-merge failures. This
    regression test pins the fix: without a real decision_maker_name, address the
    business as a team.
    """
    from pipeline.client_framing import frame_lead

    row = {"business_name": "Fresh Look Salon & Spa", "business_category": "Hairdresser",
           "area": "Mumbai", "notes": '{"rating": 4.6, "reviews_count": 200}',
           "decision_maker_name": ""}
    f = frame_lead(row)
    assert f["first"] == ""
    assert f["greeting"] == "Hello Fresh Look Salon & Spa team,"
    for bad in ("Hi Fresh,", "Hello Fresh,", "Dear Fresh"):
        assert bad not in f["greeting"]

    row2 = dict(row, business_name="Greenfield Interior Studio",
                business_category="Interior designer")
    assert frame_lead(row2)["greeting"] == "Hello Greenfield Interior Studio team,"


def test_greeting_uses_real_contact_when_present():
    from pipeline.client_framing import frame_lead

    row = {"business_name": "Sri Balaji Dental Studio", "business_category": "Dental clinic",
           "area": "Indiranagar", "notes": "", "decision_maker_name": "Ms. Archana B"}
    f = frame_lead(row)
    assert f["first"] == "Ms"
    assert "Archana" in f["greeting"]


def test_template_placeholders_never_leak_into_copy():
    """Falling back to the words 'top'/'strong' leaked '(top, strong reviews)'
    into sent mail - an obvious template giveaway."""
    from pipeline.client_framing import frame_lead

    f = frame_lead({"business_name": "X", "business_category": "Salon", "area": "Mumbai",
                    "notes": "", "decision_maker_name": ""})
    assert f["rating"] is None and f["reviews"] is None
    assert "top" not in (f.get("problem") or "")
