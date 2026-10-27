-- CLIENTFINDER v3
-- Migration 0005: derived problem framing columns on `leads`.
--
-- SETUP.md documents `pipeline/infer_problems.py` as computing these, but the
-- columns were never created, so the script could not write them. These are
-- derived/copy columns: every value is regenerated from the lead's scraped
-- observations by pipeline/problem_framing.py and is safe to recompute.

ALTER TABLE leads ADD COLUMN lead_problem TEXT;
ALTER TABLE leads ADD COLUMN why_they_pay_us TEXT;