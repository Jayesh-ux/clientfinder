# Warehouse Leads + ERPNext Pitches (IMAP-Only HTML Responses)

## Browser: Obscura + Playwright (CDP)
- Started obscura on port 9222 with --stealth
- Patched gmaps_scraper_server/scraper.py to connect via CF_CDP_ENDPOINT (connect_over_cdp)
- Using Playwright through obscura only

## Leads Generated
File: pipeline/warehouse_leads_erpnext_pitches_20261025_064044.json

10 UAE warehouse leads with ERPNext pitches:
1. Al Futtaim Logistics & Warehousing (Score: 85, No website)
2. Gulf Warehousing Company (GWC) (Score: 75, Has website)
3. Dubai South Logistics District Warehouses (Score: 85, No website)
4. Jebel Ali Free Zone (JAFZA) Warehouses (Score: 85, No website)
5. Sharjah Airport International Free Zone Warehouses (Score: 85, No website)
6. National Food Products Company Warehouse (Score: 85, No website)
7. Al Maya Group Warehousing (Score: 85, No website)
8. Emirates SkyCargo Warehouses (Score: 85, No website)
9. Tristar Transport & Warehousing (Score: 85, No website)
10. Agility Logistics Warehouses (Score: 75, Has website)

## ERPNext Pitch (HTML + Text)
Each lead includes:
- subject: "Stop stock chaos at {name} - ERPNext for Warehouses"
- html: Full HTML email with benefits (Stock, PO/SO, GRN, Barcode, Batch/Serial, Multi-warehouse)
- text: Plain text version

## IMAP-Only HTML Response Ingestion
- Script: imap_html_responses.py (reads via IMAP only, no SMTP)
- Runner: run_imap_only.py
- Instructions: IMAP_INSTRUCTIONS.md
- Uses existing email_accounts table (hsinghjayesh@gmail.com configured)
- fetch_inbox() only reads from IMAP, never sends

To fetch HTML responses:
```bash
export CF_IMAP_PASSWORD=your_app_password
cd /root/client-finder
.venv/bin/python run_imap_only.py
# or
.venv/bin/python imap_html_responses.py
```

All operations use obscura (Playwright CDP) for browsing. No direct SMTP send - IMAP only for responses.
