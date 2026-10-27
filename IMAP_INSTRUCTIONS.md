# IMAP-Only HTML Response Ingestion

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
