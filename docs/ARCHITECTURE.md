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

## What is built (13 Nov, 6:30 PM)
| Step | Built? | Where |
|---|---|---|
| Read photo (Qwen -> Gemini), read text (gpt-oss-20b -> regex) | yes | fallback.py, extract.py |
| Cross-check, fill gaps, maths, verdict | yes | maths.py, verdict.py |
| Second reading on a mismatch | yes | extract.second_reading, main.py |
| Hindi sentence + MP3 | yes | speak.py, fallback.speak |
| Telegram card + MP3, pasted SMS | yes | bot/main.py |
| Results stored | in memory only (lost on restart) | main.py `CHECKS`; db.py is task A3 |
| Cache by SHA-256 (photos) | yes: one JSON per photo in CACHE_DIR, survives a restart; a repeat makes no AI call; a missing MP3 is made again with edge-tts only | cache.py, main.py |
| Lender match | not yet: `lender.match` is null and the card hides the line (D26) | lender.py, task C1 |
| Next step | one fixed line: "Loan lene se pehle bank mitra se poochho." (D26) | main.py; next_step.py is task C2 |
| Harassment log, PDF, verify | sample data | tasks F1 to F5 |

No card -> `422 {"detail": {"code": "NOT_A_LOAN" | "UNREADABLE", "text_hi": "..."}}`; the bot and web page show `text_hi` as it is (D26).

## One photo check, step by step (POST /api/checks)
1. cache.py: SHA-256 of the image bytes. Hit -> return the stored CheckResult and MP3. Stop.
2. extract.py: ask fallback.py to read the image (Qwen first, then Flash-Lite). Strip ``` fences, parse JSON, validate with Pydantic. is_loan_ad false -> polite refusal.
3. maths.py: cross-check related numbers (within Rs 1). Derive missing ones only from numbers that were read. Compute extra, cost_pct, per_day, per_week_pct, apr_simple.
4. If the cross-check fails (photos only): second reading by the OTHER reader (Gemini after Qwen, Qwen after Gemini). Fields more than Rs 1 apart, or seen by only one reader, are disputed and set aside; numbers that then cannot be worked out are unverified. A missing key number alone does NOT trigger a second reading; it is simply "couldn't verify" (D30). Text offers never get a second reading.
5. verdict.py: cost band from config thresholds; CANNOT_SAY if a key number is unverified.
6. lender.py: RapidFuzz against data/rbi_dla.csv -> FOUND / SIMILAR / NOT_FOUND + list date.
7. next_step.py: exactly one next step for the verdict.
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
| Text reading: gpt-oss-20b | 5 s | regex for rupee amounts and days | more "couldn't verify" chips |
| Harassment labelling: gpt-oss-20b | 5 s | keyword list + time rule | H1/H6 still fire; text rules "needs review" |
| Voice out: edge-tts | 6 s | none | card alone |
| Voice-note in: Whisper (stretch) | 8 s | none | "Photo ya message bhejo" |
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
