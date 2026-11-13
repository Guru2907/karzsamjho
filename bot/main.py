"""KarzSamjho Telegram bot (long polling).

Skeleton: a photo is sent to the API and the text card comes back. No audio yet
(task D3, after D2). Only ONE program may poll a bot token at a time.

Run:  python -m bot.main
"""
import logging

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from api.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs URLs, which contain the token
log = logging.getLogger("bot")

MSG_START = "Namaste! Loan ke offer ki photo bhejo. Main bataunga kitna milega aur kitna dena hoga."
MSG_SERVER_DOWN = "Server abhi band hai, thodi der mein try karo."
MSG_BAD_PHOTO = "Photo saaf nahi hai, dobara bhejo."
MSG_SEND_PHOTO = "Loan ke offer ki photo bhejo."


def rupees(field: dict | None) -> str:
    """Format a number field as rupees, or say it could not be verified."""
    if not field or field.get("value") is None or field.get("status") == "unverified":
        return "pata nahi chala"
    return f"₹{field['value']:,.0f}"


def card_text(result: dict) -> str:
    """The formatted text card. Bold rupee numbers, four symbols."""
    n = result.get("numbers", {})
    days = n.get("tenure_days") or {}
    days_txt = f"{days['value']:.0f} din" if days.get("value") is not None else "din pata nahi chale"
    return (
        f"✅ *{rupees(n.get('in_hand'))}* haath mein\n"
        f"↩️ *{rupees(n.get('repay_total'))}* dena hai\n"
        f"\U0001f4c5 *{days_txt}*\n"
        f"⚠️ *{rupees(n.get('extra'))} zyada*\n\n"
        f"{result.get('next_step', {}).get('text_hi', '')}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_START)


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]  # the largest size
    tg_file = await photo.get_file()
    image = bytes(await tg_file.download_as_bytearray())
    try:
        async with httpx.AsyncClient(timeout=30) as http:
            r = await http.post(f"{settings.api_url}/api/checks",
                                files={"image": ("offer.jpg", image, "image/jpeg")},
                                data={"lang": "hi", "source": "telegram"})
    except httpx.HTTPError:
        log.warning("API not reachable at %s", settings.api_url)
        await update.message.reply_text(MSG_SERVER_DOWN)
        return
    if r.status_code != 200:
        log.warning("API answered %s", r.status_code)
        await update.message.reply_text(MSG_BAD_PHOTO)
        return
    await update.message.reply_text(card_text(r.json()), parse_mode=ParseMode.MARKDOWN)


async def on_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_SEND_PHOTO)


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is empty. Put your TEST bot token in .env "
                         "(only the server laptop uses the demo bot token).")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(~filters.COMMAND, on_other))
    log.info("Bot is polling. API: %s. Stop with Ctrl+C.", settings.api_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
