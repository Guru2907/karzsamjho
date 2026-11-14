# KarzSamjho

**Loan lene se pehle, suno.** (Before you take a loan, listen.)

Send a photo of a loan offer (or paste the SMS) and hear, in Hindi, what you get, what you repay and how much extra that is. If a lender is harassing you, turn the messages and calls into a dated evidence file with the right place to complain.

Built by Team Y2K Devs at COLOSSUS 3.0 (13-14 Nov 2026), FinTech track.

**New here? Read [docs/START_HERE.md](docs/START_HERE.md) first.**

## Try it
- Website and helper app: https://karzsamjho.vercel.app (the app is at `/check`; it can be installed from the browser)
- API health: https://karzsamjho-api.onrender.com/api/health (free tier: the first call after a pause can take up to a minute)
- Telegram bot: https://t.me/karzsamjho_demo_bot (answers only while the team's bot is running)

## What it does
- **Snap & hear:** photo, pasted SMS or a Hindi voice note in Telegram, or photo / SMS in the web app -> a simple card + Hindi voice; warns when an offer asks for money before the loan. Bengali and Marathi voices exist as drafts: a native speaker has not approved the sentences yet
- **Rupee receipt:** in hand, to repay, days, extra; maths in code, never by AI
- **Official next step:** is the app in RBI's directory of digital lending apps (by name and by website)? Spoken as well as shown, with the list date; a dated warning when RBI has cancelled the company's NBFC registration (exact name only); then one next action
- **Harassment log:** forward a threat to the bot (or log it in the web app) -> RBI recovery-rule matches (H1-H5; H6, five calls a day, exists in code but nothing logs calls yet) -> hash-chained record -> evidence PDF + complaint draft; a hand-edited record fails "verify"

## How it works
A vision model reads the photo; plain Python checks the numbers and does the maths; a second model re-reads when numbers disagree; anything unclear is reported as "couldn't verify". See docs/ARCHITECTURE.md.

## Folders
- `api/`: the backend (FastAPI, SQLite). All logic is in `api/core/`.
- `web/`: the public website (`/`, `/how`, `/partners`, `/join`) and the helper app (`/check`, `/cases`): React, Vite, Tailwind, shadcn/ui.
- `bot/`: the Telegram bot.
- `scripts/`: setup and run scripts for Windows (`.bat`) and Mac/Linux (`.sh`).
- `docs/`: progress log, decisions, architecture, testing, demo script, runbook.

## Run it
See docs/START_HERE.md for setup and docs/RUNBOOK.md for fixes.

## Results
625 automated tests (no internet needed; CI on every pull request).

Measured on 14 Nov 2026 with the real AI services, on the 15-offer demo pack we made ourselves (10 images + 5 SMS, expected answers written by hand first):
- Paced run (one photo every 25 s): 15 of 15 as expected, including 2 that must say "couldn't verify"; 0 wrong numbers shown as verified; median 2.3 s per check.
- A miss we found and fixed: in a faster run the backup model read a Hindi pamphlet's "₹50 हज़ार" as ₹50 and the card showed it as verified. A sanity rule now turns such a reading into "couldn't verify".
- Harassment samples: 5 of 5 get exactly the expected rules; the PDF masks the 12-digit number; a hand-edited record fails verify.
- Kill-switch drill: with a wrong Groq key the backup model answered a photo and an SMS in under 3 s; with voice off the card still arrives.

All rows: docs/TESTING.md. Team progress: `python scripts/show_progress.py`.

## Limits
Synthetic test offers only (RBI's lists are the real public files). "Not found in RBI's directory" does not mean illegal; a cancelled registration is a dated fact, not an accusation. The cost bands are our own rule of thumb, not an RBI limit. Not tested with real users yet. Free AI tiers allow about 3 photos a minute; after that the backup model reads.

## Credits
Telegram Bot API, Groq (Qwen, gpt-oss-20b, Whisper), Google Gemini API, edge-tts, FastAPI, Pydantic, RapidFuzz, ReportLab, python-telegram-bot, React, Vite, Tailwind CSS, shadcn/ui, lucide-react. AI coding tools: Claude Code, Cursor.
