import sqlite3
import sys

DB_PATH = 'crm.db'

def update_status(business_name_fragment, status_type, value):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find the lead
    cursor.execute("SELECT lead_id, business_name FROM leads WHERE business_name LIKE ?", (f"%{business_name_fragment}%",))
    matches = cursor.fetchall()

    if not matches:
        print("No leads found matching that name.")
        return
    if len(matches) > 1:
        print("Multiple leads found. Be more specific:")
        for m in matches:
            print(f" - {m['business_name']}")
        return

    lead = matches[0]
    lead_id = lead['lead_id']
    b_name = lead['business_name']

    if status_type == 'stage':
        valid_stages = ['new', 'researched', 'qualified', 'first_contact_sent', 'proposal_sent', 'won', 'lost']
        if value not in valid_stages:
            print(f"Invalid stage. Must be one of: {valid_stages}")
            return
        cursor.execute("UPDATE leads SET outreach_stage = ? WHERE lead_id = ?", (value, lead_id))
        print(f"Updated '{b_name}' stage to '{value}'")
    
    elif status_type == 'whatsapp':
        valid_wa = ['not_requested', 'requested', 'opted_in', 'opted_out']
        if value not in valid_wa:
            print(f"Invalid whatsapp status. Must be one of: {valid_wa}")
            return
        cursor.execute("UPDATE leads SET whatsapp_permission_status = ? WHERE lead_id = ?", (value, lead_id))
        print(f"Updated '{b_name}' WhatsApp status to '{value}'")

    elif status_type == 'optout':
        cursor.execute("UPDATE leads SET do_not_contact = 1, do_not_contact_reason = ?, whatsapp_permission_status = 'opted_out' WHERE lead_id = ?", (value, lead_id))
        print(f"🚨 OPT-OUT LOGGED for '{b_name}'. Reason: {value}")

    else:
        print("Invalid status type. Use: stage, whatsapp, or optout")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python update_status.py <business_name_fragment> <type(stage|whatsapp|optout)> <value>")
        print("Example: python update_status.py 'Smile Dental' stage qualified")
        print("Example: python update_status.py 'Smile Dental' whatsapp opted_in")
        print("Example: python update_status.py 'Smile Dental' optout 'Not interested'")
        sys.exit(1)
    
    update_status(sys.argv[1], sys.argv[2], sys.argv[3])
