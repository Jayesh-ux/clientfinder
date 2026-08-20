import sqlite3

DB_PATH = 'crm.db'

messages = {
    "Eva Esthetic": """Hi Dr. Eva team, I'm Rohit, a local developer in Bengaluru. 

I noticed you offer high-ticket cosmetic and implant services, but the current online flow makes it hard for patients to view a premium portfolio and book instantly via WhatsApp. 

I recently built a custom prototype specifically for high-end dental clinics to solve this. I'm open to helping you solve any other tech or patient-flow problems you're facing too. 

Would you prefer I send the booking prototype link via email, or may I send it here on WhatsApp?""",

    "Root 32": """Hi Root 32 Dental team, I'm Rohit, a local developer based here in Bengaluru (just near HRBR Layout).

Your website looks great and already supports online booking. However, I noticed there's an opportunity to automate the patient journey further—specifically around WhatsApp lead capture, automated reminders, and review requests to reduce manual staff follow-ups.

I've built a custom patient-automation and WhatsApp booking prototype for dental clinics to show how this works. I'm also open to helping you solve any other software or flow bottlenecks you have.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?""",

    "Dental Den": """Hi Dental Den team, Rohit here. I'm a developer based in Bengaluru. 

Your clinic has great reviews, but I noticed there isn't an easy, one-click way for families to book appointments online right from their phones.

I actually just built a custom appointment prototype for family dental clinics that solves this and sends automated reminders. I'm happy to help with any other online challenges you have as well.

Should I send the link to the prototype via email, or is it okay to send it here on WhatsApp?""",

    "The Dental Lounge": """Hi Dental Lounge team, I'm Rohit, a local developer. 

Your website looks great, but I noticed it relies on a standard contact form instead of an automated WhatsApp flow, which means your staff might be doing a lot of manual follow-ups.

I built a custom WhatsApp booking prototype for clinics that automates this entire process. I'm also open to tackling any other software or patient-flow issues you are facing.

Would you prefer I share the prototype via email, or may I send it directly here on WhatsApp?""",

    "Dr. Shetty's Dental": """Hi Dr. Shetty's Dental team, I'm Rohit, a local developer based here in Bengaluru.

I checked out your website and noticed some placeholder text like "Maecenas..." and repeated generic sections, which might make it confusing for new patients trying to learn about your treatments.

I've put together a modern, conversion-focused website prototype tailored specifically for dental clinics to show how we can clean this up and make booking seamless. I'm also happy to help with any other tech or digital setup you need.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?""",

    "Sure Smile Dental Care": """Hi Sure Smile Dental team, I'm Rohit, a local developer based here in Bengaluru.

I noticed your clinic has a strong online and Practo presence. While you have appointment calls-to-action on your website, it looks like there's no automated patient journey behind them (like instant WhatsApp confirmation, reminders, or recall campaigns).

I've built a custom patient-flow automation prototype that handles WhatsApp booking, instant confirmations, and automatic reminders for dental clinics. I'm also happy to assist with any other digital challenges your clinic is facing.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?""",

    "Mr Smile Dental": """Hi Mr Smile Dental team, I'm Rohit, a local developer based here in Kalyan Nagar.

I checked out your online setup and love that you already have online booking and WhatsApp follow-up in place. Because you're digitally advanced, I wanted to share a prototype for the next level: CRM-style automation for missed-lead recovery, automated patient recall, and review generation.

I've put together a custom CRM and automation flow prototype designed for busy dental practices. I'm also open to helping with any other custom software or technical integrations you might need.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?""",

    "Apollo Dental Clinic Kalyan Nagar": """Hi Apollo Dental Kalyan Nagar team, I'm Rohit, a local developer based here in Kalyan Nagar.

I checked out your clinic online and saw your website and appointment options. I noticed there's a strong opportunity to streamline this into a fully automated WhatsApp funnel that handles the entire booking, confirmation, reminder, and follow-up sequence to prevent missed appointments.

I've built a custom WhatsApp booking and patient-flow prototype for dental practices to demonstrate how this works. I'm also happy to help with any other software or API challenges you're facing.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?""",

    "Dantam Clinics": """Hi Dantam Clinics team, I'm Rohit, a software developer specializing in dental clinic automation.

I saw your excellent digital presence and online booking setup. Since you're already well-established online, my focus is on optimization: I noticed opportunities for multi-branch WhatsApp workflows, automated patient recall campaigns, and hands-free Google review generation.

I've built a custom multi-branch patient recall and automation prototype for dental practices. I'm also open to solving any other custom API, CRM, or backend issues your team is currently facing.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?""",

    "Gnathos Dental": """Hi Gnathos Dental team, I'm Rohit, a developer specializing in custom systems for dental practices.

Your modern website, online booking, and 4.9 Google rating look fantastic! Since your site is already strong, I noticed an opportunity in the backend: a custom automation/CRM layer to automatically capture leads, follow up on missed inquiries, and handle recall campaigns.

I've put together a patient-follow-up and CRM automation prototype designed specifically for high-performing dental practices. I'm also happy to help build any other custom integrations or tools your clinic needs.

Would you prefer I send the prototype link to your email, or may I share it right here on WhatsApp?""",

    "KAARA Clinics": """Hi KAARA Clinics team, I'm Rohit, a developer specializing in medical practice automation.

I checked out your active site and saw your strong review presence. Because you offer a mix of dental, skin, and hair services, there's a great opportunity to implement dental-specific lead routing, automated WhatsApp replies, and smart recall campaigns based on the service queried.

I've built a custom multi-service lead routing and WhatsApp automation prototype for clinics. I'm also open to helping with any other software development or database issues you need solved.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?""",

    "Ishaa Dental Skin & Hair Clinic": """Hi Ishaa Clinic team, I'm Rohit, a software developer specializing in practice automation.

I saw your active website and great recent reviews. Since you operate a multi-service dental, skin, and hair practice, there's a strong opportunity to use automated WhatsApp triage to qualify dental enquiries before they reach your staff, saving manual follow-up time.

I've built a custom enquiry qualification and WhatsApp scheduling prototype to show how this works. I'm also happy to help with any other web development or custom database tasks you have.

Would you prefer I send the prototype link via email, or may I share it right here on WhatsApp?"""
}

def draft_messages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for name, msg in messages.items():
        cursor.execute("UPDATE leads SET first_contact_message = ?, outreach_stage = 'qualified' WHERE business_name LIKE ?", (msg, f"%{name}%"))
        print(f"Drafted formatted message for {name}")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    draft_messages()
