import sqlite3
import os

DB_PATH = 'crm.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        lead_id TEXT PRIMARY KEY,
        created_at TEXT,
        updated_at TEXT,
        business_name TEXT,
        business_category TEXT,
        sub_category TEXT,
        city TEXT,
        area TEXT,
        pincode TEXT,
        address_public TEXT,
        website_url TEXT,
        instagram_url TEXT,
        facebook_url TEXT,
        linkedin_company_url TEXT,
        decision_maker_name TEXT,
        decision_maker_role TEXT,
        public_business_email TEXT,
        public_business_phone TEXT,
        contact_form_url TEXT,
        source_type TEXT,
        source_url TEXT,
        source_terms_checked BOOLEAN,
        extraction_method TEXT,
        date_found TEXT,
        niche TEXT,
        lead_score INTEGER,
        priority TEXT,
        owner_assigned TEXT,
        website_status TEXT,
        mobile_experience TEXT,
        page_speed_observation TEXT,
        seo_observation TEXT,
        conversion_observation TEXT,
        booking_observation TEXT,
        whatsapp_cta_present BOOLEAN,
        social_activity_observation TEXT,
        personalisation_note TEXT,
        recommended_offer TEXT,
        offer_angle TEXT,
        estimated_project_value_inr INTEGER,
        first_contact_channel TEXT,
        first_contact_date TEXT,
        first_contact_message TEXT,
        first_contact_status TEXT,
        whatsapp_number TEXT,
        whatsapp_permission_status TEXT,
        whatsapp_opt_in_at TEXT,
        whatsapp_opt_in_source TEXT,
        whatsapp_opt_in_proof_url TEXT,
        whatsapp_opt_in_text TEXT,
        whatsapp_opt_out_at TEXT,
        whatsapp_opt_out_reason TEXT,
        outreach_stage TEXT,
        last_contacted_at TEXT,
        next_action_at TEXT,
        next_action_type TEXT,
        followup_count INTEGER,
        response_status TEXT,
        meeting_date TEXT,
        proposal_sent_at TEXT,
        proposal_value_inr INTEGER,
        deal_stage TEXT,
        deal_value_inr INTEGER,
        notes TEXT,
        do_not_contact BOOLEAN,
        do_not_contact_reason TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_db()
