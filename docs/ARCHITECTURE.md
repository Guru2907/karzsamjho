# ARCHITECTURE.md: how the parts fit

The API contract and the CheckResult shape live in CLAUDE.md. This file explains the parts, the flows and the data.
State as of 17 Nov 2026 (after D60). The hackathon build is the tag `colossus-submission`; CHANGELOG.md lists what changed since.

## Big picture
```
                         ┌──────────────────────── Vercel (karzsamjho.vercel.app) ─────────────────────────┐
Funders, NGOs, judges ──►│ Public website  /  /how  /partners  /join  404   (web/src/site, `motion`)       │
                         │   laptop: "Get the app" -> QR window (vendor halftone QR -> /app)  phone: link  │
Helper's phone (PWA) ───►│ Helper app  /app  /check  /cases  /cases/:id     (web/src/pages, shadcn/ui)     │
                         └───────────────┬──────────────────────────── web/vercel.json: /api/* ────────────┘
                                         ▼
Raju's phone (Telegram) ──► bot (python-telegram-bot, long polling) ──► FastAPI  api/main.py
                            runs on Render next to the API                      │
                                                            ┌──────────────────┼────────────────────────┐
                                                            ▼                  ▼                        ▼
                                                  api/core/* (logic)   fallback.py (ONLY outside    db.py (ONLY database
                                                  maths, verdict,      calls): Groq, Gemini,        access): Neon Postgres
                                                  lender, harass,      edge-tts                     (DATABASE_URL) or SQLite
                                                  evidence, speak...
```
- **Three doors, three audiences.** The website explains (backers, partners); the helper app works on the phone (bank mitras,
  NGOs, family); the Telegram bot is Raju's own tool. The website never opens the app on a laptop (D57); the app never links
  to the website.
- **Telegram is the borrower's tool, the app is the helper's (D59).** Raju sends offers, listens, forwards threats and gets a
  case code with `/helper`. The helper opens the case with that code and does the paperwork: logging calls, photos, the
  evidence PDF, verify, closing.
- The bot and the web app are thin: they send a photo, text or event and show what comes back. All logic is in api/core/.

## Hosting
| Part | Where | Notes |
|---|---|---|
| Website + helper app | Vercel, root `web`, `npm run build` -> `dist` | `web/vercel.json` forwards `/api/*` to Render and sends every other path to index.html |
| API + Telegram bot | Render web service `karzsamjho-api`: `python -m bot.main & uvicorn api.main:app` | free tier sleeps after 15 min; UptimeRobot pings `/api/health` every 5 min. Only ONE program may poll a bot token |
| Database | Neon Postgres (free, Singapore), `DATABASE_URL` in Render's env | survives Render restarts and redeploys (D58). Render's disk (cache JSON, MP3s) still resets; both are rebuilt on demand |
| Local work, tests | SQLite file (`DB_PATH`) when `DATABASE_URL` is empty | the normal `pytest` run never touches Neon |

## One photo check (POST /api/checks)
1. cache.py: key = SHA-256 of the image bytes (+ language for bn/mr). A hit returns the stored CheckResult and makes no AI
   call. The cache file is the fast path; if it is gone (Render restart) the database is asked by the same key (D58).
2. extract.py: fallback.py reads the image (Qwen on Groq first, then Gemini Flash-Lite). Strip ``` fences, parse JSON,
   validate with Pydantic. Not a loan -> 422 with a Hindi `text_hi`.
3. maths.py: cross-check related numbers (within Rs 1); derive missing ones only from numbers that were read; compute extra,
   cost_pct, per_day, per_week_pct, apr_simple. A repay more than 10 times the loan is treated as a misreading (D55).
4. A failed cross-check (photos only): a second reading by the OTHER reader; fields the two readers disagree on become
   "couldn't verify" (D30). Text offers never get a second reading.
5. verdict.py: cost band from the thresholds in config.py; CANNOT_SAY if a key number is unverified.
6. lender.py: the app / lender name against RBI's directory (api/data/rbi_dla.csv), whole-name match (D49): >= 92 FOUND,
   80-91 SIMILAR, < 80 NOT_FOUND; a website or Play Store link in an SMS is matched too. Optional: registered NBFC
   (rbi_nbfc.csv) and a dated warning when RBI cancelled the registration (watch_list.csv, exact name only, D51).
7. next_step.py: exactly ONE next step, first match wins: money asked first -> DO_NOT_PAY_FIRST; warning list; NOT_FOUND;
   SIMILAR; then by verdict.
8. speak.py: the fixed template filled by code; edge-tts -> MP3 in AUDIO_DIR. Voice failure = card alone. A missing MP3 is
   made again from the stored sentence on first play, in the check's own language (D58).
9. db.py: save the CheckResult with engines, seconds and language.

## One harassment case
**Opening a case** (POST /api/cases) gives a random id (`case_` + 16 hex, unguessable) and an 8-digit code, made once and
never changed (D59). There is no "list every case": a case is found only by its code (`GET /api/cases/code/{code}`) or its
secret id.
- From Telegram: the first forwarded threat (or `/log`) opens the chat's case, with Raju's Telegram first name and the
  lender of the last offer he checked. The bot keeps "this chat -> this case" and his `/bhasha` language in the database,
  under an HMAC of the chat id keyed with the bot token (D59), so a restart forgets nothing. After the first threat it asks
  once for his number with Telegram's own share button and keeps only `XXXXXX 1234`.
- From the app: "New case (borrower without Telegram)", or "Being threatened? Start a case" on a check result (linked to
  that check). The phone, if typed, is masked on the phone before it is sent; the API masks again. The new code is shown
  big for the borrower to keep.

**Logging a threat** (POST /api/cases/{id}/events; JSON from the bot, a form with photos from the app):
1. harass.py: H1 (time) and H6 (calls that day) by plain code; H3 from who was contacted; H2-H5 from the words
   (gpt-oss-20b with a keyword backup). The helper's threat type can ADD a rule: death / verbal -> H2, legal -> H5,
   shaming -> H4 (D60).
2. Photos (up to 3): shrunk on the phone, then cleaned on the server (max 1600 px, re-saved as JPEG, so EXIF / GPS is gone)
   and stored in the database with their SHA-256 (D60). They are not blurred.
3. db.py: the event with hash = SHA-256(prev_hash + its fields); the first prev_hash is 64 zeros. The fields are at,
   channel, contacted, text, rules, plus threat_type and the photos' SHA-256 ONLY when present, so older events keep their
   hashes.
4. A closed case refuses new events (409 CASE_CLOSED). The bot then opens a new case and tells Raju.

**Evidence PDF** (GET /api/cases/{id}/evidence.pdf), English, built fresh from the database (F3, D60):
- Part 1 from page 1: case code, borrower, masked phone, where the case came from, Open / Closed status, rules broken,
  timeline (type, words with 12-digit numbers masked, photo numbers), every hash.
- Part 2 always from a new page: where to complain (route from the RBI match, F5) and the complaint draft (F6).
- Part 3 from a new page: the photos, two per page, each with its fingerprint.

**Verify** (GET /api/cases/{id}/verify): recomputes every link and hash from the database, and re-hashes every stored
photo. Any edit, deletion, reordering or swapped picture -> ok false (F4, D60). Closing details are not part of the chain.

**Closing** (POST /api/cases/{id}/close): a reason and an optional note; in the app the helper must type CASE CLOSED. Final,
no reopen. The record, PDF and verify stay; the day counter stops; the app lists the case under "Closed".

## The helper app (PWA)
- `/app` Home (what it does, three tiles, install button), `/check` (photo or SMS -> card, voice, full detail, "Start a
  case"), `/cases` (code box, New case, "Cases on this phone"), `/cases/:id` (code, borrower, timeline with types and
  photos, Log a threat, Evidence PDF, Verify, Close case).
- "Cases on this phone" is kept in that browser's localStorage only; the app never fetches a list of everyone's cases.
- Installable (manifest `start_url` /app). Theme applied before the first paint; the status bar follows it.

## Fallback ladder
| Dependency | Timeout | Backup | User sees if all fail |
|---|---|---|---|
| Photo reading: Qwen (Groq) | 6 s | Gemini 3.5 Flash-Lite, 12 s | "Photo saaf nahi hai, dobara bhejo" |
| Second reading (the other reader) | 12 s / 6 s | none | disputed fields shown as "couldn't verify" |
| Text reading: gpt-oss-20b | 5 s | Gemini Flash-Lite (12 s), then regex for rupee amounts and days (B11) | more "couldn't verify" |
| Harassment labelling: gpt-oss-20b | 5 s | keyword list + time rule; the threat type still adds its rule | H1/H3/H6 still fire |
| Voice out: edge-tts | 6 s | none | card alone |
| Voice-note in: Whisper | 8 s | Gemini Flash-Lite listens (12 s, B11) | "Awaaz saaf nahi aayi, dobara bolo ya photo bhejo" |
| Database: Neon | pool, 20 s | none (a cache miss is not an error) | "Server abhi band hai" |
Groq 429 -> switch to Gemini at once (never wait for retry-after).

## Free-tier budget
- Groq qwen/qwen3.8-27b: 30 req/min, 8K tokens/min, 1,000 req/day, 200K tokens/day; about 2,500 tokens per photo -> about
  3 photos/min, about 80/day. Every vision call logs its tokens and Groq's remaining tokens.
- Gemini 3.5 Flash-Lite: 15 req/min, 500/day; daily reset at 1:30 PM IST.
- Neon free: 0.5 GB; sleeps after about 5 min idle (the health ping keeps it awake). Render free: sleeps after 15 min.

## Data stored (Neon Postgres, or SQLite; same tables)
- checks: id, created_at, source, image_sha256, verdict, extra, seconds, engines, result_json, lang
- cases: id (random), code (8 digits, unique), borrower_name, borrower_phone (masked), source (telegram | app),
  telegram_chat (HMAC key, never shown), lender_name, check_id, route, opened_at, closed_at, close_reason, close_note
- events: seq, id, case_id, at, channel, contacted, text, rules, hash, prev_hash, threat_type
- photos: id, event_id, case_id, position, sha256, data (cleaned JPEG)
- chats: chat_key (HMAC), lang (the bot's /bhasha choice)
An older database gets the newer columns and tables on start-up (db.init_db). Photos and checks are never deleted by the app.

## Privacy and safety, in one place
- Synthetic test data in the repo. No login: possession of the 8-digit code (or the secret case id) is the access.
- Phones: only the last 4 digits are ever stored. 12-digit numbers in the words are masked in the PDF and on screen.
- Photos are kept as added (cleaned of hidden data, not blurred); the dialog asks helpers to cover Aadhaar or bank numbers.
- Never "illegal", "fake" or "safe" about a lender; always the RBI list date.
- Keys and DATABASE_URL live only in .env (git-ignored) and in Render's dashboard.
- Known limits: an 8-digit code can in theory be guessed (no rate limit yet); the close reason is not in the hash chain.
