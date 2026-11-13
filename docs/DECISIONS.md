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
| D24 | 13 Nov 3:10 PM | Work split: two Claude Code users build the backend and bot; two Antigravity users do wireframes, test data, printed ads and pitch; UI is built after 7:30 PM | The 7:30 PM gate needs only Telegram voice + card; splitting by tool and by file avoids two people editing the same code |
| D25 | 13 Nov 4:50 PM | Re-plan at 4:50 PM: pipeline incl. second reading for the 7:30 review; harassment, lender, db, cache after. The web /check page is built now by the PWA teammate (this replaces "UI is built after 7:30 PM" in D24). Owners, files and times are in docs/PLAN.md | Nothing was built by 4:50 PM; one working photo/text -> card + voice flow matters more than breadth |
| D26 | 13 Nov 5:00 PM | Until the lender check is built, `lender.match` is null ("not checked") and the card hides the lender line; `next_step` is one fixed line; with no card, POST /api/checks answers 422 with `{"detail": {"code": "NOT_A_LOAN" or "UNREADABLE", "text_hi"}}` | Showing "Not found in RBI's directory" for a check we did not run would mislead; the bot and the web page need one agreed shape for "no card" |
| D27 | 13 Nov 5:10 PM | Every change goes through a pull request with green CI; only Gurpreet merges; nobody pushes to main. The PWA teammate also owns web/public/ and web/index.html (for the home-screen manifest, E6) | The lead reviews each change before it lands while four people work at once; the manifest cannot live in web/src/ |
| D28 | 13 Nov 6:00 PM | Gurpreet merges with "Create a merge commit" (never squash) and "Merge without waiting for requirements". Branches that build on unmerged work start from that branch and say "merge after #N" | The ruleset needs a code-owner review and Gurpreet cannot approve his own PRs; squashing would break stacked PRs and re-create conflicts |
| D29 | 13 Nov 6:00 PM | The bot's wait for the API comes from the config timeouts: vision + 2 x read + speak + 9 s = 45 s | The worst photo check (Qwen timeout, Gemini, second reading, voice) needs 36 s; a fixed 30 s showed "server band hai" while the server was still working |
| D30 | 13 Nov 6:00 PM | Second reading runs only when the cross-check fails on a photo, not when a key number is just missing, and never for text | CLAUDE.md: "a mismatch triggers the second reading"; a missing number is already "couldn't verify"; saves Groq/Gemini quota |
| D31 | 13 Nov 6:00 PM | Readers return text like "Rs 5,000" and "2 weeks"; code turns them into numbers. Weeks = 7 days, months = 30 days, years = 365 days (our convention). A "10%" fee is worked out in code from the principal. For SMS, any number the AI gives that is not written in the message is dropped | The AI only copies; all conversion and maths stay in code; stops invented numbers like D18 |
| D32 | 13 Nov 6:50 PM | D7 is Bengali and Marathi, not Kannada: edge-tts bn-IN-TanishaaNeural and mr-IN-AarohiNeural; templates in native script (in docs/PLAN.md); card text stays Hinglish; a native speaker approves each sentence | Nobody on the team knows Kannada, so nobody could check a Kannada sentence; both voices exist and are free (no key) |
| D33 | 13 Nov 6:50 PM | POST /api/checks also takes a form field `audio` (voice note); `engines` gets an optional `listen` field; `lang` (hi, bn, mr) picks the voice | Voice notes need Whisper, which only fallback.py may call, so the bot sends the audio to the API; both changes are additive |
| D34 | 13 Nov 6:50 PM | After-review split by file: Gurpreet owns main, schemas, config, fallback, cache, db, lender, next_step, extract; Siddeshwar owns bot, speak, harass, evidence, maths, verdict. Musts first, D6/D7 only after the 7:30 gate | Two people building at once with no shared files; the harassment feature is the largest must block |
