import sqlite3
import uuid
from datetime import datetime

DB_PATH = 'crm.db'

# Define the 9 target clinics with details and approved outreach messages
clinics_data = [
    {
        "business_name": "Dr. Shetty's Dental",
        "city": "Bengaluru",
        "area": "Banaswadi",
        "pincode": "560043",
        "priority": "P1",
        "estimated_project_value_inr": 45000,
        "website_url": "http://www.shettysdental.com/",
        "public_business_phone": "08041558558",
        "personalisation_note": "Website contains obvious template/filler copy such as 'Maecenas...' and repeated generic sections. Strong opportunity for a complete modern conversion-focused redesign.",
        "message": """Hi Dr. Shetty's Dental team, I'm Rohit, a local developer based here in Bengaluru.

I checked out your website and noticed some placeholder text like "Maecenas..." and repeated generic sections, which might make it confusing for new patients trying to learn about your treatments.

I've put together a modern, conversion-focused website prototype tailored specifically for dental clinics to show how we can clean this up and make booking seamless. I'm also happy to help with any other tech or digital setup you need.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Root 32 Dental Clinic",
        "city": "Bengaluru",
        "area": "HRBR Layout",
        "pincode": "560043",
        "priority": "P1",
        "estimated_project_value_inr": 35000,
        "website_url": "",
        "public_business_phone": "+916364444636",
        "personalisation_note": "Established clinic with online booking already, so the opportunity is automation rather than basic website replacement: WhatsApp lead capture, reminders, review requests and recall campaigns.",
        "message": """Hi Root 32 Dental team, I'm Rohit, a local developer based here in Bengaluru (just near HRBR Layout).

Your website looks great and already supports online booking. However, I noticed there's an opportunity to automate the patient journey further—specifically around WhatsApp lead capture, automated reminders, and review requests to reduce manual staff follow-ups.

I've built a custom patient-automation and WhatsApp booking prototype for dental clinics to show how this works. I'm also open to helping you solve any other software or flow bottlenecks you have.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Sure Smile Dental Care",
        "city": "Bengaluru",
        "area": "Horamavu",
        "pincode": "560043",
        "priority": "P1",
        "estimated_project_value_inr": 35000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Active website and strong Practo presence, but the site presents appointment CTAs without evidence of a sophisticated automated patient journey. Good candidate for lead/reminder/recall automation.",
        "message": """Hi Sure Smile Dental team, I'm Rohit, a local developer based here in Bengaluru.

I noticed your clinic has a strong online and Practo presence. While you have appointment calls-to-action on your website, it looks like there's no automated patient journey behind them (like instant WhatsApp confirmation, reminders, or recall campaigns).

I've built a custom patient-flow automation prototype that handles WhatsApp booking, instant confirmations, and automatic reminders for dental clinics. I'm also happy to assist with any other digital challenges your clinic is facing.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Mr Smile Dental",
        "city": "Bengaluru",
        "area": "Kalyan Nagar",
        "pincode": "560043",
        "priority": "P1",
        "estimated_project_value_inr": 40000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Already has online booking + WhatsApp + follow-up language, so avoid pitching a generic website. Pitch CRM-style automation, missed-lead recovery, review automation and patient recall instead.",
        "message": """Hi Mr Smile Dental team, I'm Rohit, a local developer based here in Kalyan Nagar.

I checked out your online setup and love that you already have online booking and WhatsApp follow-up in place. Because you're digitally advanced, I wanted to share a prototype for the next level: CRM-style automation for missed-lead recovery, automated patient recall, and review generation.

I've put together a custom CRM and automation flow prototype designed for busy dental practices. I'm also open to helping with any other custom software or technical integrations you might need.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Apollo Dental Clinic Kalyan Nagar",
        "city": "Bengaluru",
        "area": "HRBR/Kalyan Nagar",
        "pincode": "560043",
        "priority": "P1",
        "estimated_project_value_inr": 40000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Has website, appointment CTA and phone, but the opportunity is to create a stronger automated WhatsApp → booking → reminder → follow-up funnel.",
        "message": """Hi Apollo Dental Kalyan Nagar team, I'm Rohit, a local developer based here in Kalyan Nagar.

I checked out your clinic online and saw your website and appointment options. I noticed there's a strong opportunity to streamline this into a fully automated WhatsApp funnel that handles the entire booking, confirmation, reminder, and follow-up sequence to prevent missed appointments.

I've built a custom WhatsApp booking and patient-flow prototype for dental practices to demonstrate how this works. I'm also happy to help with any other software or API challenges you're facing.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Dantam Clinics",
        "city": "Hyderabad",
        "area": "Gachibowli",
        "pincode": "500032",
        "priority": "P1",
        "estimated_project_value_inr": 60000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Very established digital presence and online booking, so website replacement is not the pitch. Stronger angle: automated recall, review generation, lead follow-up and WhatsApp workflows across multiple branches.",
        "message": """Hi Dantam Clinics team, I'm Rohit, a software developer specializing in dental clinic automation.

I saw your excellent digital presence and online booking setup. Since you're already well-established online, my focus is on optimization: I noticed opportunities for multi-branch WhatsApp workflows, automated patient recall campaigns, and hands-free Google review generation.

I've built a custom multi-branch patient recall and automation prototype for dental practices. I'm also open to solving any other custom API, CRM, or backend issues your team is currently facing.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Gnathos Dental",
        "city": "Hyderabad",
        "area": "Hitech City",
        "pincode": "500032",
        "priority": "P2",
        "estimated_project_value_inr": 50000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Strong modern site, online booking, WhatsApp and 4.9 Google rating. Website rebuild would be a weak pitch; automation/CRM layer is the opportunity.",
        "message": """Hi Gnathos Dental team, I'm Rohit, a developer specializing in custom systems for dental practices.

Your modern website, online booking, and 4.9 Google rating look fantastic! Since your site is already strong, I noticed an opportunity in the backend: a custom automation/CRM layer to automatically capture leads, follow up on missed inquiries, and handle recall campaigns.

I've put together a patient-follow-up and CRM automation prototype designed specifically for high-performing dental practices. I'm also happy to help build any other custom integrations or tools your clinic needs.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "KAARA Clinics",
        "city": "Hyderabad",
        "area": "Nanakramguda",
        "pincode": "500032",
        "priority": "P1",
        "estimated_project_value_inr": 45000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Active site and 123 Google reviews. Multi-service dental/skin/hair clinic creates an opportunity for dental-specific lead routing, WhatsApp automation and patient recall.",
        "message": """Hi KAARA Clinics team, I'm Rohit, a developer specializing in medical practice automation.

I checked out your active site and saw your strong review presence. Because you offer a mix of dental, skin, and hair services, there's a great opportunity to implement dental-specific lead routing, automated WhatsApp replies, and smart recall campaigns based on the service queried.

I've built a custom multi-service lead routing and WhatsApp automation prototype for clinics. I'm also open to helping with any other software development or database issues you need solved.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?"""
    },
    {
        "business_name": "Ishaa Dental Skin & Hair Clinic",
        "city": "Hyderabad",
        "area": "Gachibowli",
        "pincode": "500032",
        "priority": "P1",
        "estimated_project_value_inr": 40000,
        "website_url": "",
        "public_business_phone": "",
        "personalisation_note": "Active website and very recent 2025 reviews verify operation. Multi-service clinic makes automated dental enquiry qualification and follow-up a relevant pitch.",
        "message": """Hi Ishaa Clinic team, I'm Rohit, a software developer specializing in practice automation.

I saw your active website and great recent reviews. Since you operate a multi-service dental, skin, and hair practice, there's a strong opportunity to use automated WhatsApp triage to qualify dental enquiries before they reach your staff, saving manual follow-up time.

I've built a custom enquiry qualification and WhatsApp scheduling prototype to show how this works. I'm also happy to help with any other web development or custom database tasks you have.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?"""
    }
]

def seed_leads():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    inserted = 0
    updated = 0
    
    for c in clinics_data:
        # Check if lead already exists
        cursor.execute("SELECT lead_id, outreach_stage FROM leads WHERE business_name = ?", (c["business_name"],))
        res = cursor.fetchone()
        
        if res:
            lead_id, current_stage = res
            # If the stage is new or qualified, we keep/set it to qualified (ready for sending).
            # If it's already sent, we keep it as is but update the draft message.
            new_stage = current_stage
            if current_stage in ['new', 'qualified', 'not_contacted']:
                new_stage = 'qualified'
                
            cursor.execute("""
                UPDATE leads
                SET updated_at = ?,
                    area = ?,
                    pincode = ?,
                    priority = ?,
                    estimated_project_value_inr = ?,
                    personalisation_note = ?,
                    first_contact_message = ?,
                    outreach_stage = ?,
                    website_url = COALESCE(NULLIF(website_url, ''), ?),
                    public_business_phone = COALESCE(NULLIF(public_business_phone, ''), ?)
                WHERE lead_id = ?
            """, (
                now, c["area"], c["pincode"], c["priority"], c["estimated_project_value_inr"],
                c["personalisation_note"], c["message"], new_stage, c["website_url"],
                c["public_business_phone"], lead_id
            ))
            updated += 1
            print(f"Updated lead: {c['business_name']} (ID: {lead_id}, Stage: {new_stage})")
        else:
            lead_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO leads (
                    lead_id, created_at, updated_at, business_name, business_category, city, area, pincode,
                    website_url, public_business_phone, niche, priority, personalisation_note, 
                    estimated_project_value_inr, first_contact_message, outreach_stage, 
                    first_contact_status, whatsapp_permission_status, do_not_contact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_contacted', 'not_requested', 0)
            """, (
                lead_id, now, now, c["business_name"], "Dental Clinic", c["city"], c["area"], c["pincode"],
                c["website_url"], c["public_business_phone"], "Dental", c["priority"], c["personalisation_note"],
                c["estimated_project_value_inr"], c["message"], "qualified"
            ))
            inserted += 1
            print(f"Inserted new lead: {c['business_name']} (ID: {lead_id})")
            
    conn.commit()
    conn.close()
    print(f"Finished seeding: {inserted} inserted, {updated} updated.")

if __name__ == '__main__':
    seed_leads()
