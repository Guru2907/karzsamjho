# ARCHITECTURE.md: how the parts fit

The API contract and CheckResult shape live in CLAUDE.md. This file explains the flow.

## Big picture
```
Raju's phone (Telegram) ──► bot/main.py ──┐
Helper's browser (PWA)  ──► web/ (Vite)  ─┼──► FastAPI api/main.py ──► core/ ──► fallback.py ──► Groq / Gemini / edge-tts
                                           │                             │
                                           │                             └──► db.py (SQLite)  ·  data/rbi_dla.csv
```
- The bot and the web app are thin: they send a photo, text or event, and show what comes back.
- All logic is in api/core/. Only fallback.py talks to outside services.

## What is built (14 Nov, 12:55 AM)
| Step | Built? | Where |
|---|---|---|
| Read photo (Qwen -> Gemini), read text (gpt-oss-20b -> regex) | yes | fallback.py, extract.py |
| Cross-check, fill gaps, maths, verdict | yes | maths.py, verdict.py |
| Second reading on a mismatch | yes | extract.second_reading, main.py |
| Hindi sentence + MP3 | yes | speak.py, fallback.speak |
| Money asked before the loan (advance-fee fraud) | yes: `pay_first` from the reader + a code rule (English, Hinglish, Devanagari Hindi, Bengali, Marathi words; B9b) for SMS and voice notes -> warning first in the voice, next step DO_NOT_PAY_FIRST (D36) | extract.py, main.py |
| "5 lakh", "2 crore", "50 hazaar" | yes, converted by code (D36) | extract.py |
| Telegram card + MP3, pasted SMS, seconds stamp | yes | bot/main.py |
| Voice notes (Hindi speech) | yes: Whisper -> number words to digits (gpt-oss) -> read like an SMS (D6) | fallback.transcribe, extract.extract_from_voice |
| Bengali + Marathi voice, /bhasha | yes: bn-IN-TanishaaNeural, mr-IN-AarohiNeural; card stays Hinglish; sentences await the native-speaker OK (D7, D32) | speak.py, bot/main.py |
| Results stored | yes: SQLite file (DB_PATH, default ./karzsamjho.db); survives a restart; main.py keeps a fast in-memory copy (A3) | db.py, main.py |
| Cache by SHA-256 (photos) | yes: one JSON per photo in CACHE_DIR, survives a restart; a repeat makes no AI call; a missing MP3 is made again with edge-tts only | cache.py, main.py |
| Lender match | yes: app/lender name (RapidFuzz, generic words stripped) + any website or Play Store link in the SMS, against the local copy of RBI's directory api/data/rbi_dla.csv; a listed name with a different link = SIMILAR (possible clone); empty directory = null (not checked); spoken via C4 when present (C1, D37) | lender.py, main.py |
| Next step | yes: exactly ONE fixed Hinglish step per check, first match wins: money asked first -> DO_NOT_PAY_FIRST; lender NOT_FOUND -> NOT_IN_RBI_LIST; SIMILAR -> CHECK_APP_NAME; else by verdict: CANNOT_SAY -> SEND_CLEARER, VERY_COSTLY -> FIND_CHEAPER, COSTLY -> ASK_BANK_MITRA, USUAL -> KEEP_PAPERS. Lender not checked (null) never blocks (C2) | next_step.next_step, main.py |
| Harassment cases + events | yes: real cases in SQLite; each event gets rules from harass.label (F1) and hash = SHA-256(prev_hash + fields), first prev = 64 zeros; day counter (F2) | main.py, db.py |
| Evidence PDF | yes: built fresh from the database by evidence.build_pdf (F3), served at /api/cases/{id}/evidence.pdf; English, 12-digit numbers masked, hash chain, complaint draft addressed by the route (grievance officer / Sachet + cybercrime portal / unsure: both, F6) | evidence.py, main.py |
| Bot harassment log | yes: forward a message (or /log) -> case event -> Hindi rules -> PDF in the chat (D5) | bot/main.py |
| Verify | yes: recomputes every hash and link from the database; any edit, deletion or reordering -> ok false (F4) | main.py `chain_ok` |
| Complaint route + day counter | yes: one route per case from the RBI match (linked check, else the lender name): regulated -> grievance officer, then Ombudsman after 30 days (+ "day N of 30"); not found -> Sachet + cybercrime / 1930; similar or not checked -> both; the PDF adds police for threats (F5) | next_step.complaint_route, main.py |
| Health | yes: each engine up/down (free pings, cached 60 s), database state, can_read_photos / can_speak (A5) | fallback.ping, main.py |

No card -> `422 {"detail": {"code": "NOT_A_LOAN" | "UNREADABLE", "text_hi": "..."}}`; the bot and web page show `text_hi` as it is (D26).

## One photo check, step by step (POST /api/checks)
1. cache.py: SHA-256 of the image bytes. Hit -> return the stored CheckResult and MP3. Stop.
2. extract.py: ask fallback.py to read the image (Qwen first, then Flash-Lite). Strip ``` fences, parse JSON, validate with Pydantic. is_loan_ad false -> polite refusal.
3. maths.py: cross-check related numbers (within Rs 1). Derive missing ones only from numbers that were read. Compute extra, cost_pct, per_day, per_week_pct, apr_simple.
4. If the cross-check fails (photos only): second reading by the OTHER reader (Gemini after Qwen, Qwen after Gemini). Fields more than Rs 1 apart, or seen by only one reader, are disputed and set aside; numbers that then cannot be worked out are unverified. A missing key number alone does NOT trigger a second reading; it is simply "couldn't verify" (D30). Text offers never get a second reading.
5. verdict.py: cost band from config thresholds; CANNOT_SAY if a key number is unverified.
6. lender.py: RapidFuzz against data/rbi_dla.csv -> FOUND / SIMILAR / NOT_FOUND + list date.
7. next_step.py: exactly one next step: pay-first first, then the RBI match (not found / similar), then the verdict (C2).
8. speak.py: fill the fixed Hindi template from the numbers; edge-tts -> MP3 in AUDIO_DIR. If it fails, no audio, card still returned.
9. db.py: save the CheckResult with engines used and seconds taken. cache.py: store it.

## One harassment event (POST /api/cases/{id}/events)
1. harass.py: H1 (time) and H6 (call count) by plain code; H2-H5 by gpt-oss-20b labelling with a keyword-list backup.
2. db.py: store the event with hash = SHA-256(prev_hash + event fields).
3. evidence.py (on GET evidence.pdf): English PDF with timeline, rules matched with basis, hashes, masked 12-digit numbers, complaint draft, the route from next_step.py.

## Fallback ladder
| Dependency | Timeout | Backup | User sees if all fail |
|---|---|---|---|
| Photo reading: Qwen (Groq) | 6 s | Gemini 3.5 Flash-Lite, 12 s | "Photo saaf nahi hai, dobara bhejo"; helper page offers manual entry |
| Second reading (the other reader) | 12 s / 6 s | none | disputed fields shown as "couldn't verify" |
| Text reading: gpt-oss-20b | 5 s | Gemini Flash-Lite (12 s), then regex for rupee amounts and days (B11) | more "couldn't verify" chips |
| Harassment labelling: gpt-oss-20b | 5 s | keyword list + time rule | H1/H6 still fire; text rules "needs review" |
| Voice out: edge-tts | 6 s | none | card alone |
| Voice-note in: Whisper | 8 s | Gemini Flash-Lite listens to the audio (12 s, B11) | "Awaaz saaf nahi aayi, dobara bolo ya photo bhejo" |
| Telegram | n/a | web /check | pitch continues in browser |
| Venue Wi-Fi | checked every 30 min | phone hotspot | nothing |
| Everything | n/a | cached demo ads, then backup video | demo runs from cache |
Groq 429 -> switch to Gemini at once (never wait for retry-after).

## Free-tier budget (server account)
- Groq qwen/qwen3.8-27b: 30 req/min, 8K tokens/min, 1,000 req/day, 200K tokens/day; about 2,500 tokens per photo planned (measured 13 Nov: 1,866 to 2,062 prompt tokens + about 115 completion tokens per synthetic ad) -> about 3/min, about 80/day. Every vision call logs its tokens and Groq's remaining tokens/requests.
- Gemini 3.5 Flash-Lite: 15 req/min, 500/day; daily reset at 1:30 PM IST.
- Builders use their own keys. The server account is for the 30-offer run, rehearsals and the demo.

## Data stored (SQLite)
- checks: id, created_at, source, image_sha256, result_json, engines, seconds
- cases: id, borrower_name, lender_name, check_id, route, opened_at
- events: id, case_id, at, channel, contacted, text, rules, hash, prev_hash
