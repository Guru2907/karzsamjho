# bot/ (Telegram bot)

python-telegram-bot with long polling. The bot is thin: it sends the photo to the API and shows what comes back.

- `main.py`: `/start`, photo -> `POST /api/checks` -> formatted text card. No audio yet.

Run from the repo root: `python -m bot.main` (the API must be running).
Only ONE program may poll a bot token at a time. Builders use the TEST bot token; only the server laptop uses the demo bot token.
Tasks in docs/TASKS.md that touch this folder: D1, D3-D7.
