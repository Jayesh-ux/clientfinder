#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

# Generate ERPNext pitches for warehouses
leads = [
    {
        "name": "Al Futtaim Logistics & Warehousing",
        "website": None,
        "phone": None,
        "address": "Dubai, UAE",
        "source": "manual"
    },
    {
        "name": "Gulf Warehousing Company (GWC)",
        "website": "https://www.gwclogistics.com",
        "phone": None,
        "address": "Doha/Dubai",
        "source": "manual"
    },
    {
        "name": "Dubai South Logistics District Warehouses",
        "website": None,
        "phone": None,
        "address": "Dubai South, UAE",
        "source": "manual"
    },
    {
        "name": "Jebel Ali Free Zone (JAFZA) Warehouses",
        "website": None,
        "phone": None,
        "address": "Jebel Ali, Dubai",
        "source": "manual"
    },
    {
        "name": "Sharjah Airport International Free Zone Warehouses",
        "website": None,
        "phone": None,
        "address": "Sharjah, UAE",
        "source": "manual"
    },
    {
        "name": "National Food Products Company Warehouse",
        "website": None,
        "phone": None,
        "address": "Dubai, UAE",
        "source": "manual"
    },
    {
        "name": "Al Maya Group Warehousing",
        "website": None,
        "phone": None,
        "address": "Dubai, UAE",
        "source": "manual"
    },
    {
        "name": "Emirates SkyCargo Warehouses",
        "website": None,
        "phone": None,
        "address": "Dubai International Airport",
        "source": "manual"
    },
    {
        "name": "Tristar Transport & Warehousing",
        "website": None,
        "phone": None,
        "address": "Sharjah, UAE",
        "source": "manual"
    },
    {
        "name": "Agility Logistics Warehouses",
        "website": "https://www.agility.com",
        "phone": None,
        "address": "Dubai, UAE",
        "source": "manual"
    },
]

for lead in leads:
    lead['erp_fit_score'] = 85 if not lead.get('website') else 75
    lead['erp_fit_reasons'] = ['Warehouse operations', 'High inventory turnover potential', 'Needs ERPNext for stock management']
    lead['pitch'] = {
        'subject': f'Stop stock chaos at {lead["name"]} - ERPNext for Warehouses',
        'html': f'''<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<h2 style="color: #2e7d32;">Fix Your Warehouse Stock Chaos with ERPNext</h2>
<p>Hi,</p>
<p>I noticed <strong>{lead["name"]}</strong>. Most warehouses in UAE still manage stock, purchases, and sales across WhatsApp, Excel, and disconnected systems - leading to stockouts, overstock, and lost revenue.</p>
<p><strong>ERPNext solves this end-to-end:</strong></p>
<ul style="line-height: 1.8;">
<li><strong>Real-time Inventory</strong> - Know stock levels across all warehouses instantly</li>
<li><strong>Purchase & Sales Orders</strong> - Convert WhatsApp orders to proper POs/SOs</li>
<li><strong>Goods Receipt & Delivery Notes</strong> - Track every movement with full audit trail</li>
<li><strong>Batch/Serial & Expiry Tracking</strong> - Critical for regulated goods</li>
<li><strong>Barcode Scanning</strong> - Speed up picking, packing & receiving</li>
<li><strong>Multi-Warehouse & Transfers</strong> - Manage stock between locations</li>
<li><strong>Low Stock Alerts & Reorder Rules</strong> - Never run out again</li>
<li><strong>Reports & Dashboards</strong> - Real-time visibility of your business</li>
</ul>
<p><strong>Implementation:</strong> 2-4 weeks, tailored to your warehouse workflow. No bloat, no per-user chaos.</p>
<p>Want a <strong>15-minute demo</strong> tailored to {lead["name"]}? Just reply with <strong>YES</strong> and I'll walk you through it.</p>
<p>Regards,<br>[Your Name]<br>[Your Email/Phone]</p>
</body>
</html>''',
        'text': f'''Subject: Stop stock chaos at {lead["name"]} - ERPNext for Warehouses

Hi,

I noticed {lead["name"]}. Most UAE warehouses run on WhatsApp + Excel for stock, purchases & orders.

ERPNext gives you in one system:
- Real-time stock across all warehouses
- PO/SO/Invoice automation
- GRN, Delivery Notes, Barcode support
- Batch/Serial & Expiry tracking
- Low stock alerts & reorder points
- Multi-warehouse transfers
- Role-based access & full audit trail

Fix stockouts, prevent double-selling, save hours daily.

Want a 15-min demo tailored to {lead["name"]}? Reply YES.

Best,
[Your Name]
[Your Contact Details]'''
    }

out_dir = Path('/root/client-finder/pipeline')
out_file = out_dir / f'warehouse_leads_erpnext_pitches_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
with open(out_file, 'w') as f:
    json.dump(leads, f, indent=2)

print(f"[+] Created {len(leads)} warehouse leads with ERPNext pitches")
print(f"[+] Saved to: {out_file}")
for i,l in enumerate(leads,1):
    print(f"{i}. {l['name']} | Score: {l['erp_fit_score']} | Has website: {'Yes' if l.get('website') else 'No'}")
