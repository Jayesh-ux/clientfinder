#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/client-finder')

from service_catalog import email
from pathlib import Path
import json
from datetime import datetime

# Use the DB account, but we need password - check env
import os
from service_catalog.config import load_env
load_env()

pwd = os.environ.get('CF_IMAP_PASSWORD')
if not pwd:
    print("[!] CF_IMAP_PASSWORD not set in env/.env")
    print("[*] Creating instruction file for IMAP-only HTML response ingestion")
    out = Path('/root/client-finder/IMAP_INSTRUCTIONS.md')
    out.write_text("""# IMAP-Only HTML Response Ingestion

Only reads HTML responses via IMAP. No SMTP sending.

## Setup
Set in .env or environment:
```bash
CF_IMAP_HOST=imap.gmail.com
CF_IMAP_PORT=993
CF_IMAP_USER=hsinghjayesh@gmail.com
CF_IMAP_PASSWORD=your_app_password
```

## Fetch HTML responses
```bash
cd /root/client-finder
.venv/bin/python imap_html_responses.py
# or use the API
curl -X POST http://localhost:8001/email/inbox/pull?account_id=1
```

## Rules
- ONLY read via IMAP
- ONLY capture HTML responses
- NO auto-send
- NO SMTP operations
""")
    print(f"[+] {out}")
    sys.exit(0)

try:
    res = email.fetch_inbox(1)
    print(res)
    # Also save raw
    out_dir = Path('/root/client-finder/pipeline')
    out_file = out_dir / f'imap_html_responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(out_file, 'w') as f:
        json.dump(res, f, indent=2)
    print(f"[+] Saved to {out_file}")
except Exception as e:
    print(e)
