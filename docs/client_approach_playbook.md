# CLIENTFINDER - Client Approach & Follow-up Playbook

How we approach ANY business (from the 427 scraped leads, or future searches) and
follow up so intros become booked calls, and booked calls become paid work.

## 1. The Frame Before We Approach

Every approach is built on FOUR elements, in order:

1. **PROBLEM** - the concrete, observable fact about their business.
   - Source: scraped observations (`booking_observation`, `conversion_observation`,
     `social_activity_observation`) or, for future searches, the 30-second look at
     their website + Google listing before contacting.
   - Must be TRUE and specific: "patients can only book by phone", "no online booking
     link on your Instagram", "listings show in Google but your site has no contact form."
2. **TENSION** - why that problem HURTS. The cost of not fixing it, in their terms.
   - Missed slots, lost enquiries, no-shows, no repeat customers, competitors with a
     booking link winning the click.
   - Emotional gate: name the pain so they feel it ("every enquiry you don't answer
     same-day is a seat/patient/slot your competitor takes").
3. **SOLUTION** - OUR fix, framed as a tool for THEIR growth, not a product pitch.
   - Category-specific build: booking funnel, order form, quote automation, portfolio site.
   - Include the "pay only after you see value" de-risk and the 2-day working sample.
4. **WHO WE ARE + ASK** - two-liner credibility + one clear next step (10-min call).

If any of the four is missing, we do NOT contact the business yet.

## 2. Where the Tension Data Comes From

- Green flag tension: they ALREADY have strong ratings/reviews (they invested in
  reputation) but no booking/digital funnel to convert it. "You have 917 reviews and
  still take bookings on WhatsApp."
- Missing-site tension: no website in local Google results = losing the "near me"
  searches outright.
- Observed-frustration tension: leads manually noted frustration with phone-only ops.
- Future searches: record WHICH of these was seen before you message so the follow-up
  can reference the same proof.

## 3. Follow-up Cadence (Email)

Outreach is a SEQUENCE of touches, not one email. Follow-up is the part that actually
wins deals - most owners reply on touch 2 or 3.

| Touch | Timing | What it does |
|------|-------|-------------|
| 1. Intro | Day 0 | Problem + tension + 2-day sample + "open to full-time too" |
| 2. Replay | Day +3 to +4 | Re-anchor problem in a NEW way (never paste the same text). Add one NEW proof point: a specific gap we re-checked, or a competitor doing it better. Restate the sample offer. |
| 3. Value-drop | Day +7 | Give away a slice of the solution for free as content: "here's your Google listing's weak spot / 5 booking killers for {category}". Make them think "this person understands our business". |
| 4. Timer | Day +14 | Time-box the offer ("building 2 more free samples this month") + last call. |
| 5. Archive / call | Day +21 | If no reply and phone exists -> move to CALL target. Else mark `response_status=no-response`, move on. |

RULES (same anti-spam protocol as AGENTS.md):
- Never send the same body twice to a person. Each touch = new angle + new phrasing.
- Max 4 email touches per lead, then switch channel (phone/WhatsApp) or stop.
- Briefer each touch. Touch 2 = 4-5 lines, touch 3 = 3-4 lines.
- If they reply ANYTHING -> drop the sequence, respond human-first within 24h.

## 4. Response Triage (what replies mean)

| Their reply | Meaning | Our move |
|-------------|---------|---------|
| "How much?" | Price objection, but ACTIONABLE | Send a tiny 3-price range + sample offer; ask for the 10-min call. Do NOT quote free first; anchor with pilot price. |
| "We already have/had someone" | Not current pain | Ask the outcome question: "was it useful? what was missing?" Plants the need. Follow-up day +7 with value-drop. |
| "Not now / busy" | Still interest, bad timing | "Sure - when's the next quiet day? I'll leave one sample live for you to check." Park for 4-6 weeks, re-open with the value-drop. |
| "We're fine with what we have" | Comfortable | STOP - do not nag. Park in `followup` pool for a future angle (e.g. after a seasonal spike or renewal season). |
| Negative / abusive | - | `do_not_contact=1`, log reason, move on instantly. No argument. |
| Positive ("yes / show me") | HOT | Confirm best phone + time, book the 10-min call, PREP a 1-slide problem->tension->solution walkthrough for THEIR business. |

## 5. Tension Bank (category → proof to re-check before follow-up)

- Review-led tension: pull their rating vs nearest competitor; if competitor has fewer
  reviews but a booking link, THAT is our proof: "they win the click, not you."
- Season tension: repair/AC = pre-monsoon spike; coaching = admission months; cake =
  festive season. Timing a follow-up around their spike beats any pitch.
- Recap/repeat tension: any business that survives on repeat clients (salon, laundry,
  dryclean, gym, dental) - "your best customer re-books only when they remember to call."

## 6. Data Updates in CRM (after EVERY touch)

Update the lead row so the pipeline stays clean:
- `outreach_stage` -> first-contact | followup-1 | followup-2 | followup-3 | meeting | proposal | won | lost | parked
- `followup_count` = number of touches
- `next_action_at` = when the next scheduled touch happens
- `response_status` = no-reply | positive | price-objection | not-now | have-vendor | do-not-contact
- `last_contacted_at` = when the last message went out

All generation is DRAFT-ONLY (see `email_accounts.send_enabled`). Nothing sends
without explicit approval.

## 7. Repo tools that make this work

- `pipeline/client_framing.py` - computes PROBLEM / TENSION / SOLUTION for any lead
  (existing or newly searched); the single source of truth for approach copy.
- `pipeline/make_outreach_drafts.py` - intro-emails (touch 1).
- `pipeline/make_followup_drafts.py` - touches 2/3/4 with per-touch angle + CRM updates.
- `pipeline/update_problem_columns.py` - regenerates the export with lead_problem + why_they_pay_us.
- `pipeline/all_leads_export.csv` - the 427-lead working list (with problem + pitch).
- `pipeline/lead_dossiers.md`, `pipeline/phone_call_targets.md` - deep-dig + call sheets.