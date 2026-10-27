#!/usr/bin/env python3
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

os.environ['CF_CDP_ENDPOINT'] = 'http://127.0.0.1:9222'

from gmaps_scraper_server import scraper

WAREHOUSE_KEYWORDS = [
    "warehouse",
    "warehouses", 
    "distribution center",
    "wholesale warehouse",
    "storage warehouse",
    "industrial warehouse"
]

ERP_NEXT_PAIN_SIGNALS = [
    "no website", "phone only", "whatsapp orders", "manual stock",
    "inventory", "stock", "out of stock", "purchase order", 
    "supplier", "delivery", "dispatch"
]

def score_erp_fit(place):
    score = 0
    reasons = []
    name = (place.get('name') or '').lower()
    categories = ' '.join(place.get('categories') or []).lower()
    website = place.get('website') or ''
    phone = place.get('phone') or ''
    
    if any(k in name or k in categories for k in ['warehouse', 'wholesale', 'distribut', 'storage']):
        score += 30
        reasons.append('Warehouse/wholesale business')
    if not website:
        score += 25
        reasons.append('No website - prime for digital transformation')
    elif website and ('facebook' in website or 'instagram' in website or 'whatsapp' in website):
        score += 15
        reasons.append('Relies on social/WhatsApp for orders')
    if phone and not website:
        score += 10
        reasons.append('Phone-only operations')
    if place.get('rating') and place.get('reviews_count', 0) > 10:
        score += 10
        reasons.append('Established business')
    
    return min(score, 100), reasons

def generate_erpnext_pitch(place, score, reasons):
    name = place.get('name', 'Business')
    location = place.get('address', '')
    
    pitch_html = f"""<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
<h2>Fix Your Warehouse Stock Chaos with ERPNext</h2>
<p>Hi,</p>
<p>I noticed <strong>{name}</strong>. Most warehouses I talk to are still managing stock, purchases, and sales on WhatsApp, Excel, or paper - leading to stockouts, overstock, and lost orders.</p>
<p><strong>ERPNext can fix this in 2-4 weeks:</strong></p>
<ul>
<li><strong>Stock Control</strong> - Know exactly what's in each bin/warehouse in real-time</li>
<li><strong>Purchase & Sales</strong> - Convert WhatsApp orders to proper PO/SO/Invoices</li>
<li><strong>GRN & Delivery Notes</strong> - Track goods in/out with barcode support</li>
<li><strong>Batch/Serial Tracking</strong> - Essential for expiry/lot control</li>
<li><strong>Multi-warehouse</strong> - Manage multiple locations from one screen</li>
<li><strong>Reports & Alerts</strong> - Low stock alerts, reorder points, valuation</li>
</ul>
<p><strong>Quick wins:</strong> Stop double-selling, cut stockouts, save hours of admin daily.</p>
<p>Want a 15-min demo tailored to {name}? Reply with "yes" and I'll show you live with your actual stock scenario.</p>
<p>Best,<br>[Your Name]<br>[Your Contact]</p>
</body>
</html>"""
    
    pitch_text = f"""Subject: Stop losing money to warehouse stock chaos

Hi,

I noticed {name}. Most warehouses still run on WhatsApp + Excel for stock, purchases & orders. 

ERPNext gives you:
- Real-time stock across all warehouses
- PO/SO/Invoice in one place  
- GRN, Delivery Notes, Barcode support
- Low stock alerts & reorder points
- Batch/Serial tracking
- Multi-user with proper roles

Fix stockouts, prevent double-selling, save hours daily.

Want a 15-min demo tailored to {name}? Reply YES.

Regards,
[Your Name]"""
    
    return {
        'html': pitch_html,
        'text': pitch_text,
        'subject': f'Stop stock chaos at {name} - ERPNext for warehouses'
    }

async def hunt_warehouses(locations, max_per_location=25):
    all_leads = []
    
    for loc in locations:
        for kw in WAREHOUSE_KEYWORDS[:3]:  # Focus on key terms
            query = f"{kw} {loc}"
            print(f"[*] Scraping: {query}")
            try:
                results = await scraper.scrape_google_maps(query, max_places=max_per_location, lang='en', headless=True, concurrency=3)
                for r in results:
                    r['search_query'] = query
                    r['location_searched'] = loc
                    score, reasons = score_erp_fit(r)
                    r['erp_fit_score'] = score
                    r['erp_fit_reasons'] = reasons
                    if score >= 40:  # Only keep decent fits
                        r['pitch'] = generate_erpnext_pitch(r, score, reasons)
                        all_leads.append(r)
                print(f"    -> {len(results)} found, {sum(1 for x in results if score_erp_fit(x)[0]>=40)} qualified")
            except Exception as e:
                print(f"    [ERR] {e}")
    
    # Deduplicate by place_id or name
    seen = set()
    unique = []
    for l in all_leads:
        key = l.get('place_id') or l.get('name', '').lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(l)
    
    return unique

def main():
    locations = os.environ.get('WAREHOUSE_LOCATIONS', 'Dubai,Jebel Ali,Sharjah,Abu Dhabi').split(',')
    locations = [l.strip() for l in locations if l.strip()]
    max_per = int(os.environ.get('WAREHOUSE_MAX', '25'))
    
    print(f"[*] Hunting warehouses in: {locations}")
    print(f"[*] Using obscura CDP at http://127.0.0.1:9222")
    
    leads = asyncio.run(hunt_warehouses(locations, max_per))
    
    out_dir = Path('/root/client-finder/pipeline')
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f'warehouse_leads_erpnext_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(out_file, 'w') as f:
        json.dump(leads, f, indent=2)
    
    print(f"\n[+] Found {len(leads)} qualified warehouse leads for ERPNext")
    print(f"[+] Saved to: {out_file}")
    
    # Print summary
    for i, l in enumerate(leads[:10], 1):
        print(f"{i}. {l['name']} (score: {l['erp_fit_score']}) - {l.get('phone','N/A')} - {l.get('website','NO SITE')}")
    
    if len(leads) > 10:
        print(f"... and {len(leads)-10} more")

if __name__ == '__main__':
    main()
