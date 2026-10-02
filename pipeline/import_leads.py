import sqlite3
import csv
import sys
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / 'crm.db')

def import_csv(csv_path):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        inserted_count = 0
        for row in reader:
            # Generate UUID if missing
            lead_id = row.get('lead_id')
            if not lead_id:
                lead_id = str(uuid.uuid4())
            
            now = datetime.utcnow().isoformat()
            
            # Extract standard fields
            fields = [
                row.get('business_name', ''),
                row.get('business_category', ''),
                row.get('sub_category', ''),
                row.get('city', 'Bengaluru'),
                row.get('area', ''),
                row.get('pincode', ''),
                row.get('address_public', ''),
                row.get('website_url', ''),
                row.get('instagram_url', ''),
                row.get('facebook_url', ''),
                row.get('linkedin_company_url', ''),
                row.get('decision_maker_name', ''),
                row.get('decision_maker_role', ''),
                row.get('public_business_email', ''),
                row.get('public_business_phone', ''),
                row.get('contact_form_url', ''),
                row.get('source_type', ''),
                row.get('source_url', ''),
                bool(row.get('source_terms_checked', False)),
                row.get('extraction_method', 'manual'),
                row.get('date_found', now),
                row.get('niche', ''),
                int(row.get('lead_score', 0) if row.get('lead_score') else 0),
                row.get('priority', 'P1'),
                row.get('owner_assigned', 'Rohit'),
                row.get('website_status', 'unknown'),
                row.get('mobile_experience', 'unknown'),
                row.get('page_speed_observation', ''),
                row.get('seo_observation', ''),
                row.get('conversion_observation', ''),
                row.get('booking_observation', ''),
                bool(row.get('whatsapp_cta_present', False)),
                row.get('social_activity_observation', ''),
                row.get('personalisation_note', ''),
                row.get('recommended_offer', ''),
                row.get('offer_angle', ''),
                int(row.get('estimated_project_value_inr', 0) if row.get('estimated_project_value_inr') else 0),
                row.get('first_contact_channel', ''),
                row.get('first_contact_date', ''),
                row.get('first_contact_message', ''),
                row.get('first_contact_status', 'not_contacted'),
                row.get('whatsapp_number', ''),
                row.get('whatsapp_permission_status', 'not_requested'),
                row.get('whatsapp_opt_in_at', ''),
                row.get('whatsapp_opt_in_source', ''),
                row.get('whatsapp_opt_in_proof_url', ''),
                row.get('whatsapp_opt_in_text', ''),
                row.get('whatsapp_opt_out_at', ''),
                row.get('whatsapp_opt_out_reason', ''),
                row.get('outreach_stage', 'new'),
                row.get('last_contacted_at', ''),
                row.get('next_action_at', ''),
                row.get('next_action_type', ''),
                int(row.get('followup_count', 0) if row.get('followup_count') else 0),
                row.get('response_status', 'no_response'),
                row.get('meeting_date', ''),
                row.get('proposal_sent_at', ''),
                int(row.get('proposal_value_inr', 0) if row.get('proposal_value_inr') else 0),
                row.get('deal_stage', 'prospect'),
                int(row.get('deal_value_inr', 0) if row.get('deal_value_inr') else 0),
                row.get('notes', ''),
                bool(row.get('do_not_contact', False)),
                row.get('do_not_contact_reason', '')
            ]

            try:
                cursor.execute('''
                INSERT INTO leads (
                    lead_id, created_at, updated_at, business_name, business_category, sub_category, city, area, pincode, 
                    address_public, website_url, instagram_url, facebook_url, linkedin_company_url, decision_maker_name, 
                    decision_maker_role, public_business_email, public_business_phone, contact_form_url, source_type, 
                    source_url, source_terms_checked, extraction_method, date_found, niche, lead_score, priority, owner_assigned, 
                    website_status, mobile_experience, page_speed_observation, seo_observation, conversion_observation, 
                    booking_observation, whatsapp_cta_present, social_activity_observation, personalisation_note, 
                    recommended_offer, offer_angle, estimated_project_value_inr, first_contact_channel, first_contact_date, 
                    first_contact_message, first_contact_status, whatsapp_number, whatsapp_permission_status, whatsapp_opt_in_at, 
                    whatsapp_opt_in_source, whatsapp_opt_in_proof_url, whatsapp_opt_in_text, whatsapp_opt_out_at, 
                    whatsapp_opt_out_reason, outreach_stage, last_contacted_at, next_action_at, next_action_type, followup_count, 
                    response_status, meeting_date, proposal_sent_at, proposal_value_inr, deal_stage, deal_value_inr, notes, 
                    do_not_contact, do_not_contact_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [lead_id, now, now] + fields)
                inserted_count += 1
            except sqlite3.IntegrityError:
                print(f"Lead {lead_id} already exists. Skipping.")
            except Exception as e:
                print(f"Error inserting {row.get('business_name')}: {e}")
                
    conn.commit()
    conn.close()
    print(f"Successfully imported {inserted_count} leads.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_leads.py <path_to_csv>")
        sys.exit(1)
    import_csv(sys.argv[1])
