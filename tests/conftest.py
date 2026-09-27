import os
import sys
import tempfile
from pathlib import Path

import pytest

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

os.environ.setdefault("CLIENTFINDER_DB_PATH", str(Path(tempfile.gettempdir()) / "cf_test.db"))


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("cf") / "crm.db"
    return path


@pytest.fixture(scope="session")
def init_db_connected(db_path):
    import service_catalog.db as dbmod
    dbmod.get_db_path = lambda: db_path  # override resolution per-test-setup
    from pipeline import migrate as mig
    mig.DEFAULT_DB_PATH = db_path
    mig.migrate(db_path)
    from service_catalog.seed import seed
    seed()
    return db_path


@pytest.fixture(scope="session")
def leads_populated(init_db_connected, db_path):
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            business_name TEXT,
            business_category TEXT,
            sub_category TEXT,
            niche TEXT,
            city TEXT,
            area TEXT,
            website_status TEXT,
            seo_observation TEXT,
            conversion_observation TEXT,
            booking_observation TEXT,
            social_activity_observation TEXT,
            personalisation_note TEXT,
            recommended_offer TEXT,
            offer_angle TEXT,
            notes TEXT
        )
    """)
    conn.execute(
        "INSERT OR REPLACE INTO leads (lead_id, business_name, business_category,"
        " niche, website_status, seo_observation, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("lead-1", "Pine Valley Cafe", "Cafe", "Coffee shop",
         "has_website", "no mobile presence",
         "Relies on referrals and word of mouth; needs more customers and more "
         "leads; no systematic pipeline"))
    conn.execute(
        "INSERT OR REPLACE INTO leads (lead_id, business_name, business_category,"
        " niche, personalisation_note, notes) VALUES (?, ?, ?, ?, ?, ?)",
        ("lead-2", "Bright Construction Co", "Construction", "Contractor",
         "tracks field staff at remote sites",
         "Attendance is a problem; no reliable record of staff showing up at "
         "remote sites; manual check-in only"))
    conn.execute(
        "INSERT OR REPLACE INTO leads (lead_id, business_name, website_status,"
        " seo_observation, booking_observation, notes) VALUES (?, ?, ?, ?, ?, ?)",
        ("lead-3", "Sunrise Dental Clinic", "no_website",
         "No online presence found; does not rank for local keywords",
         "No online booking available; phone only",
         "Customers cannot find or book the business online"))
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def client(init_db_connected):
    from fastapi.testclient import TestClient
    from gmaps_scraper_server.main_api import app
    with TestClient(app) as c:
        yield c