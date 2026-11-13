# RUNBOOK.md: running and recovering

## First-time setup on any laptop
```
git clone <repo-url> && cd <repo>
copy .env.example .env        (Mac/Linux: cp)   then fill in YOUR OWN keys
python -m venv .venv
.venv\Scripts\activate        (Mac/Linux: source .venv/bin/activate)
pip install -r api/requirements.txt
cd web && npm install && cd ..
```
Builders use their own Gemini and Groq keys and the TEST bot token. Only the server laptop uses the DEMO bot token.

## Run (three terminals)
| What | Command | Notes |
|---|---|---|
| API | `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` | drop --reload on the demo laptop |
| Bot | `python -m bot.main` | long polling; one program per bot token |
| Web | `cd web && npm run dev -- --host` | Vite proxies /api to localhost:8000 |
Health check: open http://localhost:8000/api/health (add `?fresh=true` to re-check now). It shows each engine (Groq, Gemini, edge-tts) up or down with the reason, `can_read_photos`, `can_speak` and the database. Check it before going on stage

## Phones on the same network
- Laptop address: `ipconfig` -> IPv4 Address. Phone opens `http://<address>:5173`.
- Can't connect: allow Python/Node in Windows Firewall, set the network to Private, or put laptop and phone on one phone hotspot (venue Wi-Fi may block device-to-device).
- Camera button and audio work on plain http. "Add to home screen" needs HTTPS; not needed for the demo.

## When something breaks
| Symptom | Fix |
|---|---|
| Telegram "Conflict: terminated by other getUpdates" | Another program is polling the same token. Stop all other bots/test scripts |
| Groq 429 | Expected at times; fallback should switch to Gemini. If it doesn't, check fallback.py |
| Gemini 429 / RESOURCE_EXHAUSTED | Daily or per-minute quota; Qwen should answer; daily quota resets 1:30 PM IST |
| 503 "high demand" | Provider busy; fallback handles it; retry later |
| edge-tts error | Internet issue; the card is still sent; check hotspot |
| Web can't reach API | Check the Vite proxy and that the API runs with --host 0.0.0.0 |
| `ModuleNotFoundError` | venv not active, or `pip install -r api/requirements.txt` |
| Everything slow | Check network; switch to hotspot; demo uses cached ads |
| Bot says "Server abhi band hai" | The API is not running, or API_URL in .env points elsewhere. The bot waits up to 45 s (from the config timeouts) before saying this |
| Old checks gone | Checks are in `karzsamjho.db` (A3). If it was deleted or DB_PATH changed, old checks are gone; new ones still work. Never delete it before the demo |
| A photo says "Photo saaf nahi hai" | Both readers failed or nothing readable; check the API log for `read_image: engine=... failed (...)` lines (type and status only) |
| A photo keeps giving an old answer | It is cached by its exact bytes (A4). To read it fresh, stop the API and delete that photo's file in `cache/` (or the whole folder). Never delete `audio/` while cached results point at it; a missing MP3 is made again anyway |
| What did the team do last? | `python scripts/show_progress.py` (newest progress entries, D43) |
| Evidence PDF missing in the bot | The API must be running; check http://localhost:8000/api/cases/<id>/evidence.pdf in a browser |
| How many Groq photo reads are left? | API log lines `read_image: engine=qwen ok ... remaining_tokens=... remaining_requests=...` |

## Network switch-over
1. Turn off Wi-Fi, join hotspot. 2. Restart nothing; the bot reconnects. 3. Phones must use the laptop's NEW address. 4. Check /api/health.

## Server laptop rules
- Plugged in; sleep Never; lid close does nothing; no Windows updates.
- Push after every merge. A second laptop has the repo + its own .env and can become the server in 10 minutes.
- Before the pitch: copy the database, cache/ and audio/ to the second laptop so the demo ads stay cached.

## Keys
- Never commit .env or paste keys in chats. If a key leaks, delete it in the provider console and make a new one.
