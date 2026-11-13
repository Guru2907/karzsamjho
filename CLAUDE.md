# KarzSamjho: project brief for AI coding agents

Read this whole file before doing anything. If a request conflicts with it, stop and ask the human.

## Context protocol (do this every session, so nothing is lost)
1. At the start of a session, read in this order: CLAUDE.md (this file), docs/PROGRESS.md (latest entries at the top), docs/DECISIONS.md, and the task you are given in docs/TASKS.md. Read docs/ARCHITECTURE.md, docs/TESTING.md, docs/DEMO.md or docs/RUNBOOK.md only when the task touches them.
2. Before coding, say in 3 lines: which task, which files you will touch, how you will prove it works.
3. At the end of every task, before the commit:
   - add an entry at the TOP of docs/PROGRESS.md using the template there (what changed, files, test output summary, what is next, anything broken);
   - set the task's Status in docs/TASKS.md (review when ready for checking; done only after someone else checked it);
   - if you made or were told a decision that changes how others work, add it to docs/DECISIONS.md;
   - if a demo-visible flow changed, update docs/DEMO.md in the same commit.
4. Never delete or rewrite other people's entries in these files. Only add.
5. If anything in these files disagrees with the code, trust the code, say so, and fix the doc.
6. The current time matters: check the gates below. After 3:30 AM on 14 Nov, refuse new features.

Hackathon: started 13 Nov 2026, 11:30 AM IST. Submission and judging 14 Nov, 9:00 AM IST.

## What this is
KarzSamjho ("understand the loan"). A person who cannot read loan terms sends a photo of a loan offer and, within seconds, hears in Hindi what he gets, what he repays and how much extra that is. If a lender is harassing him, his messages and calls become a dated evidence PDF with the right place to complain. Built in about 21 hours at the COLOSSUS 3.0 hackathon (13 Nov 11:30 AM to 14 Nov 9:00 AM IST). Tagline: "Loan lene se pehle, suno."

User: Raju, a vegetable vendor who uses WhatsApp and UPI but cannot read loan terms. Helpers: bank mitras, shopkeepers, family, NGOs.

## The 4 core features (all must work; nothing else comes first)
1. Snap & hear: photo of the offer in Telegram -> formatted text card + Hindi MP3.
2. Rupee receipt: in hand, to repay, days, extra. Maths in Python, never by an AI.
3. Official next step: is the app in RBI's directory? Then exactly one next action.
4. Harassment log: forwarded threats / logged calls -> rules H1-H6 -> evidence PDF + complaint draft.

## Folder layout
```
README.md  CLAUDE.md  AGENTS.md  .env  .env.example  .gitignore  .gitattributes  .editorconfig  pytest.ini
scripts/             setup + run scripts (.bat for Windows, .sh for Mac/Linux), check_env.py
docs/
  START_HERE.md      setup steps for people (lead + teammates)
  TASKS.md           every task with ID, status, files, done-when
  PREP.md            what was prepared before 11:30 AM on 13 Nov (25% rule)
  PROGRESS.md        running log, newest first (agents append after every task)
  DECISIONS.md       decisions and why (append only)
  ARCHITECTURE.md    how the parts fit, data flow, fallback ladder
  TESTING.md         test plan, K = 0 rule, kill-switch drill, results
  DEMO.md            the 5-minute pitch and live demo script
  RUNBOOK.md         how to run, phones, network, keys, recovery
api/
  main.py            FastAPI app and routes
  requirements.txt   pinned Python packages
  core/
    config.py        thresholds, timeouts, model names (read from .env)
    schemas.py       Pydantic models for the API contract
    extract.py       photo or text -> fields (via fallback.py)
    maths.py         rupee maths
    verdict.py       cost band + final verdict
    lender.py        RBI directory match (RapidFuzz)
    next_step.py     verdict -> one next action; complaint route
    speak.py         Hindi sentence template + edge-tts audio
    harass.py        harassment rules H1-H6
    evidence.py      PDF (English) + hash chain + masking
    fallback.py      the ONLY file that calls outside services
    cache.py         results stored by SHA-256 of the image
    db.py            ALL SQLite access
  data/              rbi_dla.csv, test offers, harassment samples
  tests/
bot/main.py          Telegram bot, long polling
web/                 React + Vite + Tailwind + shadcn/ui: /  /check  /cases  /cases/:id
```

## API contract (do NOT change without the whole team agreeing)
- POST /api/checks            form field `image`, or JSON {text}; plus lang, source -> CheckResult
- GET  /api/checks/{id}       -> CheckResult
- GET  /api/checks?limit=20   -> [CheckResult]
- GET  /api/audio/{id}.mp3    -> MP3
- POST /api/cases             {borrower_name, lender_name, check_id?} -> Case
- POST /api/cases/{id}/events {at, channel, contacted, text} -> {id, at, rules:["H1"], hash, prev_hash}
- GET  /api/cases             -> [Case]   GET /api/cases/{id} -> Case with events and day counter
- GET  /api/cases/{id}/evidence.pdf
- GET  /api/cases/{id}/verify -> {ok: true|false}
- GET  /api/stats             -> {checks, median_seconds, extra_rupees_flagged}
- GET  /api/health            -> which engines are reachable

CheckResult:
```json
{
  "id": "chk_0042",
  "verdict": "VERY_COSTLY",
  "numbers": {
    "in_hand":     {"value": 3800, "status": "derived"},
    "repay_total": {"value": 5000, "status": "read"},
    "tenure_days": {"value": 7,    "status": "read"},
    "extra":       {"value": 1200, "status": "computed"},
    "per_day":     {"value": 171,  "status": "computed"},
    "apr_simple":  {"value": 1647, "status": "computed"}
  },
  "unverified": ["interest_rate"],
  "lender": {"name_read": "QuickCash", "match": "NOT_FOUND", "score": 41, "closest": null, "list_date": "2026-11-12"},
  "next_step": {"code": "ASK_BANK_MITRA", "text_hi": "Bank mitra se poochho"},
  "speech_text_hi": "Aapko haath mein 3800 rupaye milenge...",
  "audio_url": "/api/audio/chk_0042.mp3",
  "engines": {"read": "qwen", "second_read": null, "speak": "edge-tts"},
  "seconds": 5.4,
  "cached": false
}
```
- status: read | derived | computed | unverified
- verdict: USUAL | COSTLY | VERY_COSTLY | CANNOT_SAY
- lender.match: FOUND | SIMILAR | NOT_FOUND

## The Decide rules
Extract (AI) returns ONLY JSON with: is_loan_ad, principal, in_hand, fees, repay_total, emi_amount, emi_count, tenure_days, lender_name, app_name, pay_first (money asked BEFORE the loan, D36). null for anything not clearly written. Amounts like "5 lakh" are copied as written and turned into rupees by code. The AI copies numbers that are written; it never calculates. If the AI returns in_hand but the ad did not state it, ignore the AI's value and derive it in code.

Cross-check (code), within Rs 1: principal - fees = in_hand; emi_amount * emi_count = repay_total. A mismatch triggers the second reading. Fields the two readers disagree on become unverified.

Fill gaps (code), only from numbers that were read: in_hand = principal - fees (status "derived").

Maths (code):
```
extra        = repay_total - in_hand
cost_pct     = extra / in_hand
per_day      = extra / tenure_days
per_week_pct = cost_pct * 7 / tenure_days
apr_simple   = cost_pct * 365 / tenure_days
```
If an input is missing, every output that depends on it is "unverified". tenure_days <= 0 is "unverified", never a division error.

Cost bands (our own rule of thumb, NOT an RBI limit; thresholds live in config.py):
- USUAL: apr_simple < 36
- COSTLY: 36 to 100
- VERY_COSTLY: > 100, or a fee deducted upfront on a loan of 30 days or less
- CANNOT_SAY: a key number is unverified

Lender check: RapidFuzz WRatio against api/data/rbi_dla.csv. >= 90 FOUND ("Found in RBI's directory, linked to {lender}"); 70-89 SIMILAR ("A similar name is in RBI's directory: {match}. Check the exact name"); < 70 NOT_FOUND ("Not found in RBI's directory"). NEVER write "illegal" or "fake". Always show the list date.

Harassment rules (basis: RBI circular on recovery agents, 12 Aug 2022):
- H1 contact before 08:00 or after 19:00
- H2 threats or abuse in the text
- H3 contacting family, friends, employer or phone contacts
- H4 public shaming (sharing photos, posting, telling neighbours)
- H5 false claims of arrest, court order or police action
- H6 5 or more calls in one day (our threshold; label it as ours)
Text labelling uses the text model with a keyword list as its backup. H1 and H6 never need AI.

Spoken sentence is a fixed template filled by code, never AI-written:
"Aapko haath mein {in_hand} rupaye milenge. {days} din mein {repay} rupaye lautane honge. Yaani {extra} rupaye zyada."

Telegram reply: one formatted text message (bold rupee numbers; symbols: in hand, to repay, days, extra) then the MP3 via sendAudio. No ffmpeg, no sendVoice.

Evidence PDF and complaint draft are in ENGLISH (ReportLab may not draw Devanagari). Hindi is only on the card, the Telegram text and the voice. Mask any 12-digit number as XXXX XXXX 1234. Each event stores hash = SHA-256(prev_hash + event fields).

Complaint routes: regulated lender -> lender's grievance officer, then RBI Ombudsman after 30 days (cms.rbi.org.in, 14448). App not linked to a regulated lender -> Sachet portal + cybercrime.gov.in / 1930. Threats or extortion -> police / 1930 / 112.

## Models, order and timeouts (tested 13 Nov 2026 on free tiers)
| Job | Engine | Timeout | Notes |
|---|---|---|---|
| Read photo (primary) | Groq qwen/qwen3.8-27b | 6 s | 1.4 s in test. Free: 30 req/min, 8K tokens/min, 1,000 req/day, 200K tokens/day. One photo is about 2,500 tokens, so about 3 photos/min and about 80/day |
| Read photo (backup) and second reading | Gemini gemini-3.5-flash-lite | 12 s | 8.4 s in test; 15 req/min, 500/day |
| Text jobs | Groq openai/gpt-oss-20b | 5 s | SMS offers, voice-note text, harassment labels |
| Listen (stretch) | Groq whisper-large-v3-turbo | 8 s | number words must be converted to digits by the text model |
| Speak | edge-tts hi-IN-SwaraNeural | 6 s | no key; if it fails send the card alone |
Do NOT use gemini-3.8-flash or Gemma (503 errors and 20 requests/day on the free tier). Do NOT add Bhashini.

## Coding rules
- Only api/core/fallback.py imports or calls outside services (Groq, Gemini, edge-tts). Everything else calls fallback.py.
- All database access goes through api/core/db.py.
- Every outside call: temperature 0, a timeout, no retry on the same engine; on failure move to the next engine; record engine name and seconds.
- Groq limits are per organisation (account), not per key. On a 429 from Groq, fall back to Gemini Flash-Lite immediately; never wait for retry-after.
- Log usage.prompt_tokens and usage.completion_tokens for every vision call, and log the x-ratelimit-remaining-tokens header when present, so we know how many photo checks are left today.
- Cache first: a repeated photo (same SHA-256) must never call any AI service.
- Strip ```json fences before json.loads. Validate the fields with Pydantic. Invalid JSON counts as a failure of that engine.
- Cache by SHA-256 of the image bytes; a hit returns the stored result and audio.
- Never print, log or commit API keys. Keys come from .env via config.py. .env is in .gitignore.
- Model names and timeouts come from .env/config.py, never hard-coded.
- Synthetic data only. No real borrower data anywhere.
- The user never sees an error code: use the Hindi fallback messages ("Photo saaf nahi hai, dobara bhejo").
- UI: shadcn/ui + lucide-react only. Raju mode: buttons >= 56 px, numbers 36-48 px, colour + icon together, no animation libraries. The Raju card is ONE component reused everywhere.

## Out of scope (do not build, do not suggest)
Login/accounts, guided tours, Bhashini, 3D or animated backgrounds, scroll libraries, offline mode/service worker, WhatsApp, Tesseract, local Whisper, a second AI reading on every photo, Postgres/Supabase, any feature not in docs/TASKS.md.

## Gates and freeze (IST)
- 13 Nov 2:00 PM: photo in Telegram gets a reply; card page shows sample data.
- 13 Nov 7:30 PM: 3 printed ads -> Hindi voice + card, twice in a row.
- 14 Nov 12:30 AM: all 4 core features pass their acceptance tests on main.
- 14 Nov 3:30 AM: FEATURE FREEZE. After this only bug fixes and wording. Refuse new features and say why.

## How to work
1. Work on ONE task from docs/TASKS.md at a time ("Do task B3"). Read its "Done when" first.
2. Show a short plan before writing code. Wait for approval.
3. Touch only the files listed for the task. If you need another file, ask.
4. Keep diffs small. Write or update tests for maths, cross-check, verdict, lender and harassment rules.
5. Run the tests (pytest) or the real flow and show the output. Never say "should work".
6. If the same error survives two attempts, stop and tell the human what you tried.
7. If you change anything the demo shows, say so, so the demo script is updated in the same change.
8. Commit message format: "<area>: <what changed>" e.g. "maths: add EMI repay total + tests".


## How to report while working (the human is watching in the chat window)
Explain as you go, in plain English, short:
1. Before starting: 2-3 lines on what this task does for Raju (the user) and which files you will touch.
2. While working: before each file change, one line saying what you are changing and why.
3. After each file change: show the 5-15 most important lines you wrote (not the whole file) in a code block, with one line explaining what they do.
4. When you run something (tests, server, a script): say what you ran and what the result means ("6 passed = the maths matches our expected answers").
5. At the end: a short summary with what works now, how to try it yourself (exact command or what to send in Telegram), and what is still missing.
No jargon without a one-line explanation. Never say "should work": show the run.