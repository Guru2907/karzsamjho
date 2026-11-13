# KarzSamjho

**Loan lene se pehle, suno.** (Before you take a loan, listen.)

Send a photo of a loan offer and hear, in Hindi, what you get, what you repay and how much extra that is. If a lender is harassing you, turn the messages and calls into a dated evidence file with the right place to complain.

Built by Team Y2K Devs at COLOSSUS 3.0 (13-14 Nov 2026), FinTech track.

**New here? Read [docs/START_HERE.md](docs/START_HERE.md) first.**

## What it does
- **Snap & hear:** photo, pasted SMS or a Hindi voice note in Telegram -> a simple card + voice in Hindi, Bengali or Marathi; warns when an offer asks for money before the loan
- **Rupee receipt:** in hand, to repay, days, extra; maths in code, never by AI
- **Official next step:** is the app in RBI's directory of digital lending apps (by name and by website)? Spoken as well as shown, with the list date; then one next action
- **Harassment log:** forward a threat to the bot -> RBI recovery-rule matches (H1-H6) -> hash-chained record -> evidence PDF + complaint draft

## How it works
A vision model reads the photo; plain Python checks the numbers and does the maths; a second model re-reads when numbers disagree; anything unclear is reported as "couldn't verify". See docs/ARCHITECTURE.md.

## Folders
- `api/`: the backend (FastAPI, SQLite). All logic is in `api/core/`.
- `web/`: the frontend (React, Vite, Tailwind, shadcn/ui).
- `bot/`: the Telegram bot.
- `scripts/`: setup and run scripts for Windows (`.bat`) and Mac/Linux (`.sh`).
- `docs/`: progress log, decisions, architecture, testing, demo script, runbook.

## Run it
See docs/START_HERE.md for setup and docs/RUNBOOK.md for fixes.

## Results
440 automated tests (no internet needed; CI on every pull request). Measured real runs, misses included: docs/TESTING.md. Team progress: `python scripts/show_progress.py`.

## Limits
Synthetic test data only. "Not found in RBI's directory" does not mean illegal. Not tested with real users yet.

## Credits
Telegram Bot API, Groq (Qwen, gpt-oss-20b, Whisper), Google Gemini API, edge-tts, FastAPI, Pydantic, RapidFuzz, ReportLab, python-telegram-bot, React, Vite, Tailwind CSS, shadcn/ui, lucide-react. AI coding tools: Claude Code, Cursor.
