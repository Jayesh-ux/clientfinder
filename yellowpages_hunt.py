#!/usr/bin/env python3
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

def fetch_html(url):
    try:
        result = subprocess.run(['obscura', 'fetch', url, '--dump', 'html', '--stealth'], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"ERR: {e}")
        return ""

def parse_yellowpages(html):
    leads = []
    # Look for business listings
    # Pattern varies, try to find common patterns
    # Look for company names
    patterns = [
        r'<h[23][^>]*>([^<]+)</h[23]>',
        r'class="[^"]*company[^"]*"[^>]*>([^<]+)<',
        r'class="[^"]*title[^"]*"[^>]*>([^<]+)<',
    ]
    for p in patterns:
        matches = re.findall(p, html, re.I)
        for m in matches:
            m = m.strip()
            if len(m) > 3 and 'warehouse' in m.lower():
                leads.append({
                    'name': m,
                    'source': 'yellowpages.ae',
                    'erp_fit_score': 70,
                    'website': None,
                    'phone': None,
                    'address': None,
                    'pitch': {
                        'subject': f'Stop stock chaos at {m} - ERPNext for warehouses',
                        'html': f'<html><body><h2>ERPNext for {m}</h2><p>Manage stock, PO/SO, GRN across warehouses in one place. Reply YES for demo.</p></body></html>',
                        'text': f'Subject: ERPNext for warehouses\n\nHi {m},\n\nTired of WhatsApp orders & Excel stock? ERPNext gives real-time inventory, purchase/sales, delivery notes, low-stock alerts.\n\nWant 15-min demo? Reply YES.'
                    }
                })
    return leads

def main():
    urls = [
        'https://www.yellowpages.ae/search/warehouses/dubai',
        'https://www.yellowpages.ae/search/warehouse/sharjah',
        'https://www.yellowpages.ae/search/logistics/dubai',
    ]
    all_leads = []
    for url in urls:
        print(f"[*] Fetching {url}")
        html = fetch_html(url)
        leads = parse_yellowpages(html)
        print(f"    -> {len(leads)} found")
        all_leads.extend(leads)
    
    # Deduplicate
    seen = set()
    unique = []
    for l in all_leads:
        k = l['name'].lower()
        if k in seen: continue
        seen.add(k)
        unique.append(l)
    
    out_dir = Path('/root/client-finder/pipeline')
    out_file = out_dir / f'warehouse_leads_erpnext_yp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(out_file, 'w') as f:
        json.dump(unique, f, indent=2)
    print(f"\n[+] {len(unique)} leads saved to {out_file}")
    for i,l in enumerate(unique[:10],1):
        print(f"{i}. {l['name']}")

if __name__ == '__main__':
    main()
