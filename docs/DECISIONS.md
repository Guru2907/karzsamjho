# DECISIONS.md: what we decided and why (append only)

Add new decisions at the bottom with the time. If a decision is reversed, add a new entry; do not edit the old one.

| # | When | Decision | Why |
|---|---|---|---|
| D1 | Round 1 | User is Raju, a vegetable vendor who cannot read loan terms; helpers are bank mitras, shopkeepers, family, NGOs | A specific user with a specific friction (reading) |
| D2 | Round 1 | Answer by voice in rupees plus a simple card; no reading needed | Removes the friction; our main difference from LoanLens / V.A.R.U.N. |
| D3 | 10 Nov | Exactly 4 core features: Snap & hear, Rupee receipt, Official next step, Harassment log | Promised in the Round 1 deck; scope control after AfterHours |
| D4 | 10 Nov | The AI only reads; all maths, cross-checks, verdicts and rules are plain Python with tests | A wrong rupee number is the one failure we cannot have (K = 0) |
| D5 | 10 Nov | Unknown numbers are "couldn't verify", never guessed; a key unknown makes the verdict CANNOT_SAY | Honesty and safety |
| D6 | 10 Nov | Never call a lender "illegal" or "fake"; only "Not found in RBI's directory" | The directory is self-reported by lenders; names vary |
| D7 | 10 Nov | Cost bands (36% / 100%) and "5 calls a day" are our own thresholds in config, not RBI limits | No single RBI cap applies to all app loans |
| D8 | 10 Nov | Frontends: Telegram bot (Raju), one React PWA (/check with Raju mode, /cases, /cases/:id), one landing page (/) as stretch | Three surfaces only; no other websites |
| D9 | 10 Nov | One FastAPI server on the lead's laptop; SQLite; bot uses long polling | Works on any network, no public URL needed |
| D10 | 10 Nov | Only api/core/fallback.py calls outside services; all DB access in api/core/db.py | One place to handle timeouts, fallbacks and logging |
| D11 | 10 Nov | Out of scope: login, tours, 3D/animated backgrounds, offline mode, WhatsApp, Tesseract, Postgres | AfterHours lesson: scope explosion |
| D12 | 10 Nov | Feature freeze at 3:30 AM on 14 Nov | AfterHours lesson: late changes broke the demo |
| D13 | 10 Nov | Demo runs on 3 printed ads that are pre-run and cached | The demo must not depend on luck |
| D14 | 10 Nov | Bhashini dropped | API keys need an institutional profile and manual approval |
| D15 | 13 Nov 02:30 | Reader order: Groq qwen/qwen3.8-27b (1.4 s) first, Gemini gemini-3.5-flash-lite (8.4 s, 12 s timeout) second; Flash-Lite also does the second reading | Measured in prep/test_keys.py |
| D16 | 13 Nov 02:30 | gemini-3.8-flash and Gemma dropped | 503 errors in testing; 3.8 Flash allows only 20 free requests/day |
| D17 | 13 Nov 02:30 | Temperature 0 for every AI call; strip code fences; validate with Pydantic | Same photo, same answer; Qwen wrapped JSON in fences |
| D18 | 13 Nov 02:30 | Code derives in_hand; the AI's computed numbers are ignored | Flash-Lite invented in_hand 3800 although the ad did not state it |
| D19 | 13 Nov 02:40 | Telegram reply = formatted text (bold rupee numbers, 4 symbols) + MP3 via sendAudio; no ffmpeg | Proven with prep/tg_test.py |
| D20 | 13 Nov | Evidence PDF and complaint draft in English; Hindi only on card, Telegram text and voice | ReportLab may not draw Devanagari correctly |
| D21 | 13 Nov 03:10 | On a Groq 429, fall back to Gemini immediately; log tokens for every vision call; each person builds with their own Groq and Gemini keys | Groq free tier ~80 photo reads/day per account; limits are per organisation |
| D22 | 13 Nov | Voice-note numbers go through gpt-oss-20b to convert number words to digits | Whisper wrote "with" for "seven" (saath/saat) |
| D23 | 13 Nov 1:30 PM | Only README.md, CLAUDE.md and AGENTS.md (+ config dotfiles) stay at the top; TASKS.md, PREP.md and START_HERE.md live in docs/ | Cleaner top folder; Claude Code and Cursor only auto-read CLAUDE.md / AGENTS.md from the top |
