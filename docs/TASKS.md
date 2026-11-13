# TASKS.md: KarzSamjho task list

How to use: pick one task by ID ("Do task B3"). Status is one of: todo, doing (name), review, done. Change the Status line when you start, when it is ready for checking, and when someone else has checked it. Read CLAUDE.md first. Touch only the files listed. A task is finished only when its "Done when" is true on the main branch and someone who did not build it has checked it.

Type: M = must build. S = stretch, only after the 7:30 PM gate on 13 Nov has passed. Nothing new after the 3:30 AM freeze on 14 Nov.

## Right now: the 7:30 PM review (re-plan at 4:50 PM, D25)

Owners, order, target times and signatures are in docs/PLAN.md. In scope tonight:
- Lead: A4 (without the cache), A6, A7, B1, B2, B6, B7, B8
- Claude Code teammate: B3, B4, B5, D2, D3, D4
- PWA teammate: E2, E3, E9, E6, E7
- Data teammate: G3, G8, then G1, G2, G4; also I1 (mentor questions) and I3 (backup video)

After the review: owners and order are in docs/PLAN.md, "After the review" (D34). Gurpreet: seconds stamp on the card and A4 now, then A3, A5, F2, F4, C1, C2, F5, no D6/D7 (D35). Siddeshwar: D6 and D7 in full after the 7:30 gate, then F1, F3, D5. PWA teammate: all E tasks. Data teammate: G1 to G4, G8, I1, I3.

Waiting until after the review: A3 (database), the cache half of A4, A5, C1 to C3, D5, E4, E5, E8, all of F.
All changes go through a pull request that Gurpreet merges (D27).

## A. Server and setup

### A1 · Create repo, `docs/PREP.md`, `.env.example`, `.gitignore`
- Status: review
- Type: Must
- Depends on: -
- Files: docs/PREP.md, README.md, .env.example, .gitignore
- Done when: First commit is pushed by 12:00 PM and `.env` is not in it

### A2 · API with stub answers for every endpoint
- Status: review
- Type: Must
- Depends on: A1
- Files: api/main.py
- Done when: Every route in section 5 returns sample data by 12:30 PM

### A3 · `db.py`: tables for checks, cases, events
- Status: todo
- Type: Must
- Depends on: A1
- Files: api/core/db.py
- Done when: A check and a case survive a server restart

### A4 · `fallback.py` + `cache.py`
- Status: review (Gurpreet): speak, read_image, read_text (5:40 PM) and the photo cache (7:00 PM) done
- Type: Must
- Depends on: A2
- Files: api/core/fallback.py, api/core/cache.py
- Done when: With the Groq key removed, a check still answers through Gemini Flash-Lite; a repeated photo answers instantly

### A5 · `/api/health`, `/api/stats`
- Status: todo (partly: /api/stats counts the in-memory checks; /api/health shows keys set, not engines reachable)
- Type: Must
- Depends on: A3
- Files: api/main.py
- Done when: Health lists each engine as up or down; stats numbers match the database

### A6 · Seconds stamp and engine names on every result
- Status: review (fallback side: every read returns engine + seconds; A7 puts them on the CheckResult)
- Type: Must
- Depends on: A4
- Files: api/main.py, api/core/fallback.py
- Done when: Each `CheckResult` has `seconds` and `engines` filled

### A7 · Join the parts in `POST /api/checks`; results kept in memory
- Status: review (Gurpreet)
- Type: Must
- Depends on: A4, B1, B3, B5, D2
- Files: api/main.py, api/core/schemas.py, api/tests/test_pipeline.py, api/tests/test_smoke.py
- Done when: A photo or a text offer returns a real `CheckResult` (not the sample); `GET /api/checks/{id}` and `/api/audio/{id}.mp3` work until the server restarts; not-a-loan and unreadable inputs return status 422 with a Hindi message; `lender.match` is null
- Note: added in the 4:50 PM re-plan (D25, D26). The database (A3) replaces the in-memory store later.

## B. Reading and maths

### B1 · `extract.py`: photo → fields with Qwen (temperature 0, fences stripped, fields validated)
- Status: review (Gurpreet): synthetic ad read correctly; printed ads still to test
- Type: Must
- Depends on: A4
- Files: api/core/extract.py
- Done when: The 3 printed ads, photographed by phone, return correct fields

### B2 · Text input → fields with gpt-oss-20b
- Status: review (Gurpreet)
- Type: Must
- Depends on: A4
- Files: api/core/extract.py
- Done when: A pasted SMS offer returns fields

### B3 · `maths.py` + unit tests
- Status: done (built by Siddeshwar; checked by agent for Gurpreet 6:00 PM: hand-worked table, real runs)
- Type: Must
- Depends on: A1
- Files: api/core/maths.py, api/tests/test_maths.py
- Done when: 12 tests pass: normal, fee upfront, EMI, missing field, mismatch, zero days

### B4 · Cross-check and fill gaps
- Status: done (built by Siddeshwar; checked by agent for Gurpreet 6:00 PM: contradicting ad -> CANNOT_SAY, missing in-hand derived, real run)
- Type: Must
- Depends on: B3
- Files: api/core/maths.py, api/tests/test_maths.py
- Done when: A contradictory ad is flagged; a missing in-hand amount is derived and marked "derived"

### B5 · `verdict.py` with thresholds in a config file
- Status: done (built by Siddeshwar; checked by agent for Gurpreet 6:00 PM: threshold test, real verdicts)
- Type: Must
- Depends on: B3
- Files: api/core/verdict.py, api/core/config.py
- Done when: Changing a threshold changes the verdict without touching code

### B6 · Second reading by the other reader on mismatch
- Status: review (Gurpreet)
- Type: Must
- Depends on: B1, B4
- Files: api/core/extract.py
- Done when: A disputed field becomes "couldn't verify"; an agreed field is kept

### B7 · Not-a-loan detection
- Status: review (Gurpreet)
- Type: Must
- Depends on: B1
- Files: api/core/extract.py
- Done when: A photo of a menu gets a polite refusal, not a card

### B8 · Regex backup for text offers
- Status: review (Gurpreet)
- Type: Must
- Depends on: B2
- Files: api/core/extract.py, api/tests/test_extract.py
- Done when: With the text model switched off, "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days." still returns principal 5000, fees 500, repay 5600, days 7, and `engines.read` is "regex"
- Note: added in the 4:50 PM re-plan (D25).

### B9 · Warn when an offer asks for money before the loan (advance-fee fraud)
- Status: review (Gurpreet)
- Type: Must (added 7:30 PM by the lead after the data teammate's scam texts, D36)
- Depends on: B1, B2
- Files: api/core/extract.py, api/main.py, api/tests/test_advance_fee.py
- Done when: "Pay ₹1,499 processing fee to release funds" -> next step DO_NOT_PAY_FIRST and the voice starts with the fixed "Savdhaan!" warning; a normal offer and a fee deducted from the loan get no warning

### B10 · Read "5 lakh", "2 crore", "50 hazaar", "5k" as rupees
- Status: review (Gurpreet)
- Type: Must (added 7:30 PM, D36)
- Depends on: B1, B2
- Files: api/core/extract.py, api/tests/test_advance_fee.py
- Done when: "₹5 lakh" -> 500000 from the AI path and the regex path, and is not dropped as an invented number

## C. Lender check and next step

### C1 · Load `rbi_dla.csv`; `lender.py` with RapidFuzz
- Status: todo
- Type: Must
- Depends on: A1, G4
- Files: api/core/lender.py, api/data/rbi_dla.csv, api/tests/test_lender.py
- Done when: A listed app returns FOUND with its lender; a made-up app returns NOT_FOUND; a near-miss spelling returns SIMILAR

### C2 · `next_step.py`
- Status: todo (tonight a fixed next step in main.py, D26)
- Type: Must
- Depends on: B5, C1
- Files: api/core/next_step.py
- Done when: Every verdict maps to exactly one next step

### C3 · NBFC list as a second source
- Status: todo
- Type: Stretch
- Depends on: C1
- Files: api/core/lender.py
- Done when: Only if it loads in under 20 minutes

## D. Bot and voice

### D1 · Bot receives a photo and calls the API
- Status: review
- Type: Must
- Depends on: A2
- Files: bot/main.py
- Done when: A photo sent in Telegram returns the stub reply by 2:00 PM
- Note: bot/main.py skeleton exists (photo → API → text card); D1 = make it robust + wire audio after D2.

### D2 · `speak.py`: template sentence + edge-tts audio
- Status: done (built by Siddeshwar; checked by agent for Gurpreet 6:00 PM: real MP3 in 1.5 to 3 s, numbers match the card)
- Type: Must
- Depends on: B3
- Files: api/core/speak.py
- Done when: An MP3 is produced in under 5 seconds; numbers match the card

### D3 · Bot sends formatted text + MP3
- Status: review (Siddeshwar; fixes in #11: 45 s wait, Indian commas, tests). Card + MP3 proven through the real API with Telegram faked; real Telegram with the 3 printed ads still to do
- Type: Must
- Depends on: D1, D2
- Files: bot/main.py
- Done when: Both arrive for all 3 printed ads; with voice switched off, the text still arrives

### D4 · Bot accepts pasted text offers
- Status: review (Siddeshwar). Pasted SMS proven through the real API with Telegram faked; real Telegram still to do
- Type: Must
- Depends on: B2, D1
- Files: bot/main.py
- Done when: A pasted SMS returns a reply

### D5 · Bot: forward a message → harassment event; send the PDF back
- Status: todo
- Type: Must
- Depends on: F2, F3
- Files: bot/main.py
- Done when: A forwarded message creates a case event and the PDF arrives in the chat

### D6 · Voice-note input with Whisper
- Status: review (Siddeshwar, D35): server side + bot side built; proven with the real API and real Whisper (Telegram faked); real Telegram voice note still to do
- Type: Stretch
- Depends on: D3, B2
- Files: bot/main.py (Siddeshwar); api/core/fallback.py, api/core/extract.py, api/main.py, api/core/schemas.py (Gurpreet)
- Done when: A spoken offer in Hindi returns a reply; number words become digits through gpt-oss-20b (D22); engines.listen = "whisper" (D33). Only after the 7:30 gate

### D7 · Bengali and Marathi voice (was Kannada; changed 6:50 PM, D32)
- Status: todo (Siddeshwar, all of it: templates, voices, lang through the API, /bhasha, D35)
- Type: Stretch
- Depends on: D2
- Files: api/core/speak.py, bot/main.py (Siddeshwar); api/main.py, api/core/config.py, api/core/fallback.py (Gurpreet)
- Done when: With lang bn or mr, the same check returns the MP3 in that language (bn-IN-TanishaaNeural, mr-IN-AarohiNeural), numbers match the card; a native speaker approved each sentence. Templates in docs/PLAN.md. Last; only after the 7:30 gate

## E. Helper web app

### E1 · Vite + Tailwind + shadcn setup, colour tokens for light and dark, 4 empty routes
- Status: review
- Type: Must
- Depends on: A1
- Files: web/ (setup files)
- Done when: All routes open; tokens exist for both themes

### E2 · The Raju card component
- Status: todo
- Type: Must
- Depends on: E1
- Files: web/src/components/RajuCard.tsx
- Done when: Renders the sample `CheckResult` correctly on a phone-width screen, including grey "couldn't verify" state

### E3 · `/check` with helper details and manual entry
- Status: todo
- Type: Must
- Depends on: E2, A2
- Files: web/src/pages/Check.tsx
- Done when: A photo uploaded from a phone returns the card; details table matches the API

### E4 · `/cases` list
- Status: todo
- Type: Must
- Depends on: E1, F2
- Files: web/src/pages/Cases.tsx
- Done when: Shows cases with route badge and day counter

### E5 · `/cases/:id` detail: timeline, rule badges, log dialog, PDF button, complaint draft, verify line
- Status: todo
- Type: Must
- Depends on: E4, F3
- Files: web/src/pages/CaseDetail.tsx
- Done when: A new event appears without a page reload; PDF downloads; verify shows ✓

### E6 · Manifest so the app can be added to a home screen
- Status: todo
- Type: Must
- Depends on: E1
- Files: web/public/manifest.json, icons
- Done when: Manifest has name, icons (192 and 512 px), start URL, display mode
- Note: moved into tonight's PWA work (D27). Also allowed: web/index.html (manifest link, theme-color, apple-touch-icon, viewport-fit). Added done when: "Add to home screen" in Chrome on a phone opens /check without the browser bar.

### E7 · Raju mode (details hidden, big camera and play buttons)
- Status: todo
- Type: Stretch (first stretch)
- Depends on: E3
- Files: web/src/pages/Check.tsx
- Done when: A person can complete a check without reading a word

### E8 · Phone-width, empty-state and error-state pass
- Status: todo
- Type: Must
- Depends on: E3, E4, E5
- Files: web/src/
- Done when: Every page looks right at 400 px wide, with no data and with the server off

### E9 · `/check`: text box, audio player, loading / error / not-a-loan states
- Status: todo
- Type: Must
- Depends on: E2
- Files: web/src/pages/Check.tsx, web/src/lib/api.ts
- Done when: A pasted SMS offer returns the card; the MP3 plays on a phone; a 422 answer shows its Hindi message; with the server off the page says so; the lender line is hidden when `lender.match` is null
- Note: added in the 4:50 PM re-plan (D25). E7 (Raju mode) is also in scope for the review.

## F. Evidence and harassment

### F1 · `harass.py`: rules H1–H6, text labelling with keyword backup
- Status: todo
- Type: Must
- Depends on: A4
- Files: api/core/harass.py, api/tests/test_harass.py
- Done when: The 10 samples get exactly the expected rules; the polite 11 AM reminder matches none

### F2 · Events endpoint with hash chain
- Status: todo
- Type: Must
- Depends on: A3, F1
- Files: api/main.py, api/core/db.py
- Done when: Each event stores its hash and the previous hash

### F3 · `evidence.py`: PDF with timeline, rules, hashes, masking, complaint draft
- Status: todo
- Type: Must
- Depends on: F2
- Files: api/core/evidence.py
- Done when: A forwarded message becomes a PDF in under 60 seconds; a 12-digit number is masked

### F4 · Verify endpoint
- Status: todo
- Type: Must
- Depends on: F2
- Files: api/main.py
- Done when: Editing one stored entry by hand makes verify fail

### F5 · Route chooser and day counter
- Status: todo
- Type: Must
- Depends on: C1, F2
- Files: api/core/next_step.py
- Done when: Regulated lender → grievance officer route with "Day N of 30"; unlisted app → Sachet + cybercrime route

## G. Testing and data

### G1 · 30 synthetic offers with expected answers (before the event)
- Status: todo
- Type: Must
- Depends on: -
- Files: api/data/offers/
- Done when: Images and an answers file exist; answers were written before any run

### G2 · 10 harassment samples with expected rules (before the event)
- Status: todo
- Type: Must
- Depends on: -
- Files: api/data/harassment/
- Done when: File exists

### G3 · 3 demo ads printed in colour, two copies each (before the event)
- Status: todo
- Type: Must
- Depends on: G1
- Files: (paper)
- Done when: In the folder

### G4 · RBI directory saved as CSV with its date (before the event)
- Status: todo
- Type: Must
- Depends on: -
- Files: api/data/rbi_dla.csv
- Done when: File exists with app and lender columns

### G5 · Independent "done when" checks
- Status: doing: B3, B4, B5, D2 checked 6:00 PM by agent for Gurpreet; Gurpreet's tasks (A6, A7, B1, B2, B6, B7, B8) need someone else
- Type: Must
- Depends on: the task being checked
- Files: (no code)
- Done when: Every must-task above is checked by someone who did not build it

### G6 · Full 30-offer run, paced
- Status: todo
- Type: Must
- Depends on: B1–B7, C1, G1
- Files: api/tests/run_offers.py, results file
- Done when: Results table filled; K (wrong numbers shown as verified) is known

### G7 · Kill-switch drill at 1:00 AM
- Status: todo
- Type: Must
- Depends on: A4, D3
- Files: (no code)
- Done when: All four drills in section 13 pass

### G8 · 5 SMS-style text offers with expected numbers
- Status: todo
- Type: Must
- Depends on: -
- Files: api/data/offers/sms_offers.json
- Done when: File exists with 5 offers; expected in_hand, repay_total, tenure_days and extra were worked out by hand before any run
- Note: added in the 4:50 PM re-plan (D25). The 3 demo ads (G3) also get `api/data/offers/demo_expected.json`.

## H. Landing page

### H1 · Split hero with the real card in a phone frame; top bar with theme toggle
- Status: todo
- Type: Stretch
- Depends on: E2
- Files: web/src/pages/Landing.tsx
- Done when: Looks right in light and dark, on phone and laptop

### H2 · Live numbers from `/api/stats`
- Status: todo
- Type: Stretch
- Depends on: A5, H1
- Files: web/src/pages/Landing.tsx
- Done when: Numbers change after a new check

### H3 · Story, how it works, who it helps, limits, footer
- Status: todo
- Type: Stretch
- Depends on: H1
- Files: web/src/pages/Landing.tsx
- Done when: Present; if time is short, these are the first to drop

## I. Pitch and demo

### I1 · Mentor questions for both rounds
- Status: todo
- Type: Must
- Depends on: -
- Files: (notes)
- Done when: 3 risky questions written before each round

### I2 · Deck in the framework order (section 14)
- Status: todo
- Type: Must
- Depends on: G6 for the numbers
- Files: (deck)
- Done when: 8–9 slides, real numbers filled in after the test run

### I3 · Backup video
- Status: todo
- Type: Must
- Depends on: D3
- Files: (video)
- Done when: A 60-second clip at 7:30 PM; a full run at 3:00 AM

### I4 · Roadmap-vs-actual slide
- Status: todo
- Type: Must
- Depends on: -
- Files: (deck)
- Done when: Deck's 5 blocks beside real commit times

### I5 · README
- Status: todo
- Type: Must
- Depends on: -
- Files: README.md
- Done when: What it is, how to run it, test results, limits, credits for libraries and APIs

### I6 · Three timed rehearsals
- Status: todo
- Type: Must
- Depends on: I2
- Files: (no code)
- Done when: Under 5:00 each, with the fallback moves practised once

## Acceptance tests for the 4 core features (the 12:30 AM gate)

- Snap & hear: the 3 printed ads, photographed on a phone in Telegram, each return Hindi audio + the text card. With the Groq key removed, Gemini Flash-Lite still answers. With voice switched off, the card still arrives.
- Rupee receipt: 12 maths tests pass. Across the 30 offers, no wrong number is ever shown as verified.
- Official next step: listed app -> FOUND with lender; made-up app -> NOT_FOUND; near-miss -> SIMILAR. Each verdict gives exactly one next step.
- Harassment log: 10 samples get the expected rules. A forwarded message becomes a PDF in under 60 seconds. Editing a stored entry makes verify fail. A 12-digit number is masked.
