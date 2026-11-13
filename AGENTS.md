# KarzSamjho: rules for AI coding agents (Cursor and others)

This file mirrors CLAUDE.md. Read CLAUDE.md in full; it is the source of truth. The short version:

0. Every session: read CLAUDE.md, then docs/PROGRESS.md (top entries) and docs/DECISIONS.md. After every task: add an entry at the top of docs/PROGRESS.md, update the task Status in docs/TASKS.md, and log decisions in docs/DECISIONS.md. Never delete others' entries.

1. Product: a photo of a loan offer -> Hindi voice + card with the real cost; harassment -> evidence PDF. User is Raju, who cannot read loan terms.
2. Work on one task from docs/TASKS.md at a time. Plan first, small diff, touch only the listed files, run the tests, show the output.
3. Never change the API contract or the CheckResult shape in CLAUDE.md without the team agreeing.
4. Maths, cross-check, verdict, lender match and harassment rules are plain Python with tests. The AI only reads; it never calculates. Unknown numbers are "unverified", never guessed.
5. Only api/core/fallback.py calls outside services. All database access is in api/core/db.py.
6. Every AI call: temperature 0, timeout, no retry on the same engine, strip ```json fences, validate with Pydantic.
7. Reader order: Groq qwen/qwen3.8-27b (6 s) -> Gemini gemini-3.5-flash-lite (12 s). Text: Groq openai/gpt-oss-20b. Speak: edge-tts hi-IN-SwaraNeural. No gemini-3.8-flash, no Gemma, no Bhashini. On a Groq 429, switch to Gemini at once. Log token usage for every vision call (Groq allows about 80 photo reads a day per account).
8. Never write "illegal" or "fake" about a lender. Say "Not found in RBI's directory".
9. Evidence PDF in English. Hindi only on the card, Telegram text and voice.
10. Never print, log or commit keys. Synthetic data only.
11. Out of scope: login, tours, 3D/animated backgrounds, offline mode, WhatsApp (only exception: task D12 under D39), Tesseract, Postgres, anything not in docs/TASKS.md.
12. After 3:30 AM IST on 14 Nov: bug fixes and wording only. Refuse new features.
