import sqlite3
import datetime
import json
import os

DB_PATH = 'crm.db'
TRACKER_PATH = 'queue_tracker.json'

def load_tracker():
    if os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_tracker(tracker):
    with open(TRACKER_PATH, 'w') as f:
        json.dump(tracker, f, indent=4)

def get_daily_queue():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    tracker = load_tracker()

    print("=" * 50)
    print("🚀 DAILY TASK QUEUE 🚀")
    print("=" * 50)

    # 1. New leads to research
    cursor.execute("SELECT lead_id, business_name, area, niche, outreach_stage, whatsapp_permission_status FROM leads WHERE outreach_stage = 'new' AND do_not_contact = 0")
    new_leads = cursor.fetchall()
    
    new_leads_to_show = []
    for lead in new_leads:
        state = f"{lead['outreach_stage']}_{lead['whatsapp_permission_status']}"
        if tracker.get(lead['lead_id']) != state:
            new_leads_to_show.append(lead)
            tracker[lead['lead_id']] = state

    print(f"\n[RESEARCH] {len(new_leads_to_show)} new leads need personalization research:")
    for lead in new_leads_to_show:
        print(f"  - {lead['business_name']} ({lead['area']})")

    # 2. Ready to send
    cursor.execute("SELECT lead_id, business_name, public_business_email, public_business_phone, outreach_stage, whatsapp_permission_status FROM leads WHERE outreach_stage = 'qualified' AND do_not_contact = 0")
    ready_leads = cursor.fetchall()
    
    ready_leads_to_show = []
    for lead in ready_leads:
        state = f"{lead['outreach_stage']}_{lead['whatsapp_permission_status']}"
        if tracker.get(lead['lead_id']) != state:
            ready_leads_to_show.append(lead)
            tracker[lead['lead_id']] = state

    print(f"\n[OUTREACH] {len(ready_leads_to_show)} leads approved and ready for first contact:")
    for lead in ready_leads_to_show:
        contact = lead['public_business_email'] or lead['public_business_phone'] or 'No contact info'
        print(f"  - {lead['business_name']} -> {contact}")

    # 3. Awaiting WhatsApp opt-in
    cursor.execute("SELECT lead_id, business_name, outreach_stage, whatsapp_permission_status FROM leads WHERE whatsapp_permission_status = 'requested' AND do_not_contact = 0")
    waiting_leads = cursor.fetchall()
    
    waiting_leads_to_show = []
    for lead in waiting_leads:
        state = f"{lead['outreach_stage']}_{lead['whatsapp_permission_status']}"
        if tracker.get(lead['lead_id']) != state:
            waiting_leads_to_show.append(lead)
            tracker[lead['lead_id']] = state

    print(f"\n[WAITING] {len(waiting_leads_to_show)} leads asked for WhatsApp permission:")
    for lead in waiting_leads_to_show:
        print(f"  - {lead['business_name']}")

    # 4. Opted-In (Action required)
    cursor.execute("SELECT lead_id, business_name, outreach_stage, whatsapp_permission_status FROM leads WHERE whatsapp_permission_status = 'opted_in' AND outreach_stage != 'proposal_sent' AND do_not_contact = 0")
    opted_in = cursor.fetchall()
    
    opted_in_to_show = []
    for lead in opted_in:
        state = f"{lead['outreach_stage']}_{lead['whatsapp_permission_status']}"
        if tracker.get(lead['lead_id']) != state:
            opted_in_to_show.append(lead)
            tracker[lead['lead_id']] = state

    print(f"\n[ACTION] {len(opted_in_to_show)} leads OPTED IN for WhatsApp audits:")
    for lead in opted_in_to_show:
        print(f"  - {lead['business_name']} (SEND AUDIT)")

    print("\n" + "=" * 50)
    
    save_tracker(tracker)
    conn.close()

if __name__ == '__main__':
    get_daily_queue()
