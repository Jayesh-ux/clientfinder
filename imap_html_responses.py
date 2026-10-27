#!/usr/bin/env python3
import imaplib
import email
from email.header import decode_header
import json
import os
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

def get_imap_creds():
    # Try to get from env
    host = os.environ.get('CF_IMAP_HOST') or os.environ.get('IMAP_HOST')
    port = int(os.environ.get('CF_IMAP_PORT') or os.environ.get('IMAP_PORT') or '993')
    user = os.environ.get('CF_IMAP_USER') or os.environ.get('IMAP_USER')
    password = os.environ.get('CF_IMAP_PASSWORD') or os.environ.get('IMAP_PASSWORD')
    return host, port, user, password

def fetch_html_responses(limit=50):
    host, port, user, password = get_imap_creds()
    if not all([host, user, password]):
        print("[!] Missing IMAP creds. Set CF_IMAP_HOST/CF_IMAP_USER/CF_IMAP_PASSWORD or IMAP_*")
        return []
    
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select('INBOX')
        
        # Search for unseen/unread or all
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            return []
        
        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # Get recent ones
        
        responses = []
        for e_id in reversed(email_ids):
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            if status != 'OK':
                continue
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = ''
            if msg['Subject']:
                try:
                    decoded = decode_header(msg['Subject'])[0]
                    if isinstance(decoded[0], bytes):
                        subject = decoded[0].decode(decoded[1] or 'utf-8')
                    else:
                        subject = decoded[0]
                except:
                    subject = str(msg['Subject'])
            
            from_addr = msg.get('From', '')
            date = msg.get('Date', '')
            
            html_body = None
            text_body = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition'))
                    if 'attachment' in content_disposition:
                        continue
                    if content_type == 'text/html':
                        try:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or 'utf-8'
                            html_body = payload.decode(charset, errors='ignore')
                        except:
                            pass
                    elif content_type == 'text/plain' and text_body is None:
                        try:
                            payload = part.get_payload(decode=True)
                            charset = part.get_content_charset() or 'utf-8'
                            text_body = payload.decode(charset, errors='ignore')
                        except:
                            pass
            else:
                content_type = msg.get_content_type()
                try:
                    payload = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
                    if content_type == 'text/html':
                        html_body = body
                    else:
                        text_body = body
                except:
                    pass
            
            if html_body:
                soup = BeautifulSoup(html_body, 'html.parser')
                # Remove scripts/styles
                for s in soup(['script', 'style']):
                    s.decompose()
                clean_text = soup.get_text(separator=' ', strip=True)
            elif text_body:
                clean_text = text_body
            else:
                clean_text = ''
            
            responses.append({
                'id': e_id.decode(),
                'from': from_addr,
                'subject': subject,
                'date': date,
                'has_html': html_body is not None,
                'html_body': html_body,
                'text_body': text_body,
                'clean_text': clean_text[:5000]
            })
        
        mail.close()
        mail.logout()
        return responses
    except Exception as e:
        print(f"[ERR] {e}")
        return []

def main():
    print("[*] Fetching HTML responses via IMAP only (no SMTP send)")
    responses = fetch_html_responses(limit=100)
    
    out_dir = Path('/root/client-finder/pipeline')
    out_file = out_dir / f'imap_html_responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(out_file, 'w') as f:
        json.dump(responses, f, indent=2)
    
    print(f"[+] Fetched {len(responses)} emails with HTML content")
    print(f"[+] Saved to: {out_file}")
    for i,r in enumerate(responses[:5],1):
        print(f"{i}. From: {r['from'][:40]} | Subject: {r['subject'][:50]} | HTML: {r['has_html']}")

if __name__ == '__main__':
    main()
