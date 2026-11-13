"""KarzSamjho Telegram bot (long polling). Tasks D1, D3, D4.

Raju sends a photo of a loan offer, or pastes an SMS offer. The bot asks the API,
then replies with:
  1. one text card (verdict, bold rupee numbers with 4 symbols, lender line, next step);
  2. the Hindi MP3 through sendAudio (no ffmpeg, no sendVoice). If there is no
     audio_url or the download fails, the card goes alone.
On a 422 (not a loan / unreadable) the bot replies with the API's detail.text_hi.
Raju never sees an error code or English error text.

Only ONE program may poll a bot token at a time.
Run:  python -m bot.main
"""
import html
import logging

import httpx
from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from api.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs URLs, which contain the token
log = logging.getLogger("bot")

# How long to wait for the API, from the engine timeouts in config.py (never hard-coded).
# Worst photo check: Qwen times out, Gemini reads it, the sums fail so the other reader
# reads it again, then the voice: 6 + 12 + 12 + 6 = 36 s. Plus a margin for the network.
API_TIMEOUT_S = (settings.vision_timeout_s + 2 * settings.read_timeout_s
                 + settings.tts_timeout_s + 9)          # 45 s with the default timeouts
AUDIO_TIMEOUT_S = 10
MAX_TEXT_CHARS = 2000  # an SMS offer is short; ignore pasted essays

MSG_START = ("Namaste! Loan ke offer ki photo bhejo, ya SMS yahan chipkao. "
             "Main bataunga kitna milega, kitna lautana hoga aur kitna zyada.")
MSG_SERVER_DOWN = "Server abhi band hai, thodi der mein try karo."
MSG_BAD_PHOTO = "Photo saaf nahi hai, dobara bhejo."
MSG_BAD_TEXT = "Yeh offer samajh nahi aaya. Loan ka SMS poora chipkao, ya photo bhejo."
MSG_SEND_PHOTO = "Loan ke offer ki photo bhejo, ya SMS yahan chipkao."
MSG_TOO_LONG = "Yeh bahut lamba hai. Sirf loan wala SMS chipkao."
MSG_ERROR = "Kuch gadbad hui, dobara try karo."

VERDICT_LINE = {
    "USUAL": "🟢 <b>Aam loan jaisa kharcha</b>",
    "COSTLY": "🟠 <b>Mehenga loan</b>",
    "VERY_COSTLY": "🔴 <b>Bahut mehenga loan</b>",
    "CANNOT_SAY": "⚪ <b>Pakka nahi keh sakte</b>: kuch number saaf nahi padhe gaye",
}


def _http(timeout: float) -> httpx.AsyncClient:
    """One place that makes HTTP clients (the API is on our own laptop)."""
    return httpx.AsyncClient(timeout=timeout)


def indian_digits(value: float) -> str:
    """Whole rupees with Indian grouping: 3800 -> "3,800", 100000 -> "1,00,000"."""
    digits = str(int(round(value)))
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join([head, *groups, tail])


def rupees(field: dict | None) -> str:
    """A number field as rupees ("₹3,800", "₹1,00,000"), or "pata nahi chala" when it could not be verified."""
    if not field or field.get("value") is None or field.get("status") == "unverified":
        return "pata nahi chala"
    return f"₹{indian_digits(field['value'])}"


def lender_line(lender: dict | None) -> str | None:
    """RBI directory line, or None when the check was not run (match is null).

    Never says "illegal" or "fake" (CLAUDE.md); always shows the list date.
    """
    if not lender or not lender.get("match"):
        return None
    date = html.escape(str(lender.get("list_date") or "?"))
    name = html.escape(str(lender.get("closest") or lender.get("name_read") or ""))
    match = lender["match"]
    if match == "FOUND":
        return f"🏦 RBI ki digital loan app list mein mila: {name} (list: {date})"
    if match == "SIMILAR":
        return f"🏦 RBI ki list mein milta-julta naam hai: {name}. Sahi naam check karo (list: {date})"
    return f"🏦 RBI ki digital loan app list mein nahi mila (list: {date})"


def card_text(result: dict) -> str:
    """The text card (HTML). Verdict, then 4 symbols with bold rupee numbers."""
    n = result.get("numbers") or {}
    days = n.get("tenure_days") or {}
    if days.get("value") is not None and days.get("status") != "unverified":
        days_txt = f"{days['value']:.0f} din"
    else:
        days_txt = "din pata nahi chale"
    extra = n.get("extra")
    extra_txt = (f"{rupees(extra)} zyada" if rupees(extra) != "pata nahi chala"
                 else "zyada: pata nahi chala")
    lines = [
        VERDICT_LINE.get(result.get("verdict"), VERDICT_LINE["CANNOT_SAY"]),
        "",
        f"✅ <b>{rupees(n.get('in_hand'))}</b> haath mein",
        f"↩️ <b>{rupees(n.get('repay_total'))}</b> lautana hai",
        f"\U0001f4c5 <b>{days_txt}</b>",
        f"⚠️ <b>{extra_txt}</b>",
    ]
    lender = lender_line(result.get("lender"))
    next_step = (result.get("next_step") or {}).get("text_hi")
    if lender or next_step:
        lines.append("")
    if lender:
        lines.append(lender)
    if next_step:
        lines.append(f"👉 {html.escape(next_step)}")
    return "\n".join(lines)


def no_card_text(r: httpx.Response, fallback_msg: str) -> str:
    """Hindi message for an answer without a card. A 422 carries detail.text_hi."""
    if r.status_code == 422:
        try:
            text_hi = r.json()["detail"]["text_hi"]
            if isinstance(text_hi, str) and text_hi.strip():
                return text_hi
        except (ValueError, KeyError, TypeError):
            pass
        return fallback_msg
    return MSG_ERROR


async def ask_api(update: Update, fallback_msg: str, **request) -> dict | None:
    """POST /api/checks. Returns the CheckResult, or replies in Hindi and returns None."""
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        async with _http(API_TIMEOUT_S) as http:
            r = await http.post(f"{settings.api_url}/api/checks", **request)
    except httpx.HTTPError:
        log.warning("API not reachable at %s", settings.api_url)
        await update.message.reply_text(MSG_SERVER_DOWN)
        return None
    if r.status_code != 200:
        log.warning("API answered %s", r.status_code)
        await update.message.reply_text(no_card_text(r, fallback_msg))
        return None
    try:
        return r.json()
    except ValueError:
        log.warning("API answered 200 without JSON")
        await update.message.reply_text(MSG_ERROR)
        return None


async def send_result(update: Update, result: dict) -> None:
    """The card first, then the MP3 if there is one. A voice problem never stops the card."""
    await update.message.reply_text(card_text(result), parse_mode=ParseMode.HTML)
    audio_url = result.get("audio_url")
    if not audio_url:
        return
    try:
        async with _http(AUDIO_TIMEOUT_S) as http:
            r = await http.get(f"{settings.api_url}{audio_url}")
        if r.status_code != 200 or not r.content:
            log.warning("audio not available (%s) for %s", r.status_code, result.get("id"))
            return
        await update.message.chat.send_action(ChatAction.UPLOAD_VOICE)
        await update.message.reply_audio(audio=r.content, filename=f"{result.get('id', 'karzsamjho')}.mp3",
                                         title="KarzSamjho", performer="KarzSamjho")
    except Exception as exc:  # network, Telegram: the card already went, so just log
        log.warning("audio not sent for %s: %s", result.get("id"), type(exc).__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_START)


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]  # the largest size
    tg_file = await photo.get_file()
    image = bytes(await tg_file.download_as_bytearray())
    result = await ask_api(update, MSG_BAD_PHOTO,
                           files={"image": ("offer.jpg", image, "image/jpeg")},
                           data={"lang": "hi", "source": "telegram"})
    if result:
        await send_result(update, result)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text(MSG_SEND_PHOTO)
        return
    if len(text) > MAX_TEXT_CHARS:
        await update.message.reply_text(MSG_TOO_LONG)
        return
    result = await ask_api(update, MSG_BAD_TEXT,
                           json={"text": text, "lang": "hi", "source": "telegram"})
    if result:
        await send_result(update, result)


async def on_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_SEND_PHOTO)


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is empty. Put your TEST bot token in .env "
                         "(only the server laptop uses the demo bot token).")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(~filters.COMMAND, on_other))
    log.info("Bot is polling. API: %s. Stop with Ctrl+C.", settings.api_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
