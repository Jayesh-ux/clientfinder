-- CLIENTFINDER v3
-- Migration 0004: rich-HTML body support for email drafts.
-- Additive only. Plain text `body` stays the required field; html_body is the
-- optional alternative part rendered with the {{TOKEN}} engine
-- (pipeline/html_email_render.py). send_draft emits multipart/alternative
-- when html_body is present.

ALTER TABLE email_drafts ADD COLUMN html_body TEXT;