"""KarzSamjho Telegram bot (long polling). Tasks D1, D3, D4, D6, D7.

Raju sends a photo of a loan offer, pastes an SMS offer, or speaks it (voice note, D6).
The bot asks the API, then replies with:
  1. one text card (verdict, bold rupee numbers with 4 symbols, lender line, next step);
  2. the Hindi MP3 through sendAudio (no ffmpeg, no sendVoice). If there is no
     audio_url or the download fails, the card goes alone.
On a 422 (not a loan / unreadable) the bot replies with the API's detail.text_hi.
Raju never sees an error code or English error text.
/bhasha (D7): three buttons pick the voice language (Hindi, Bangla, Marathi), remembered per
chat and sent as `lang` on every check. The card text stays Hinglish; only the voice changes.
Harassment log (D5): a forwarded text message, or a message after /log, becomes an event in
this chat's case (created once, id remembered); the bot says in Hindi which rules it broke and
sends the English evidence PDF. /pdf sends the latest PDF again.

Only ONE program may poll a bot token at a time.
Run:  python -m bot.main
"""
import html
import logging
from datetime import datetime, timedelta, timezone

import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest, NetworkError
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

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
MAX_VOICE_S = 60       # a loan offer fits in a minute; longer notes cost Whisper time and quota

MSG_START = ("Namaste! Loan ke offer ki photo bhejo, SMS yahan chipkao, ya bolkar bhejo (voice note). "
             "Main bataunga kitna milega, kitna lautana hoga aur kitna zyada. "
             "Awaaz Bangla ya Marathi mein chahiye? /bhasha dabao.")
MSG_BAD_VOICE = "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."
MSG_VOICE_TOO_LONG = "Awaaz 1 minute se lambi hai. Chhota bolo: sirf loan ki rakam, din aur kitna lautana hai."
MSG_SERVER_DOWN = "Server abhi band hai, thodi der mein try karo."
MSG_BAD_PHOTO = "Photo saaf nahi hai, dobara bhejo."
MSG_BAD_TEXT = "Yeh offer samajh nahi aaya. Loan ka SMS poora chipkao, ya photo bhejo."
MSG_SEND_PHOTO = "Loan ke offer ki photo bhejo, ya SMS yahan chipkao."
MSG_TOO_LONG = "Yeh bahut lamba hai. Sirf loan wala SMS chipkao."
MSG_ERROR = "Kuch gadbad hui, dobara try karo."

# Harassment log (D5). Hindi only for Raju; the PDF itself is English (D20).
IST = timezone(timedelta(hours=5, minutes=30))
MSG_LOG_ASK = ("Dhamki ya pareshan karne wala message yahan chipkao, ya seedha forward karo. "
               "Main use darj karke aapka saboot (PDF) bana dunga.")
MSG_LOG_EMPTY = "Message khaali hai. Dhamki wala message chipkao ya forward karo."
MSG_LOGGED = "Darj ho gaya. Is message mein yeh niyam toote: {rules}."
MSG_LOGGED_NONE = "Darj ho gaya. Is message mein koi niyam nahi toota, phir bhi saboot mein rakh liya."
MSG_PDF_CAPTION = ("Yeh aapka saboot hai (PDF, English mein). Bank mitra, shikayat ya police ko dikhayein. "
                   "Har naya message isme judta jayega.")
MSG_PDF_LATER = "Message darj ho gaya, par PDF abhi nahi ban paya. Thodi der mein /pdf bhejo."
MSG_NO_CASE = "Abhi koi shikayat darj nahi hai. Dhamki wala message forward karo, ya /log bhejo."
RULE_HI = {
    "H1": "H1 raat ya subah jaldi sampark (8 baje se pehle ya 7 baje ke baad)",
    "H2": "H2 dhamki ya gaali",
    "H3": "H3 parivaar, doston ya office se sampark",
    "H4": "H4 sabke saamne beizzati",
    "H5": "H5 police, jail ya court ka dar",
    "H6": "H6 ek din mein 5 ya zyada call (hamari seema)",
}

# /bhasha (D7): button label -> lang sent to the API. Labels in each language's own script.
LANGUAGES = (("Hindi", "hi"), ("বাংলা", "bn"), ("मराठी", "mr"))
MSG_PICK_LANG = "Awaaz kis bhasha mein chahiye? Ek button dabao. (Card Hinglish mein hi rahega.)"
MSG_LANG_SET = {
    "hi": "Theek hai: ab awaaz Hindi mein aayegi.",
    "bn": "Theek hai: ab awaaz Bangla (বাংলা) mein aayegi.",
    "mr": "Theek hai: ab awaaz Marathi (मराठी) mein aayegi.",
}

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
    if not lender:
        return None
    warning = lender.get("warning")
    if isinstance(warning, dict) and warning.get("name"):         # D51: RBI cancelled the registration
        wname = html.escape(str(warning["name"]))
        wdate = html.escape(str(warning.get("date") or "?"))
        return f"⚠️ RBI ne is company ka NBFC registration radd kiya hai: <b>{wname}</b> (list: {wdate})"
    if not lender.get("match"):
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
    seconds = result.get("seconds")
    if result.get("cached") is True:                  # D10: a repeat photo, answered from the cache
        lines.append("⏱ <b>pehle se jaancha hua</b>")  # "checked before", not a puzzling "0.0 sec"
    elif isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and seconds >= 0:
        lines.append(f"⏱ <b>{seconds:.1f} sec</b>")      # how fast Raju got the answer (DEMO LIVE 1)
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


def chat_lang(context: ContextTypes.DEFAULT_TYPE | None) -> str:
    """The voice language this chat picked with /bhasha; Hindi until he picks one."""
    chat_data = getattr(context, "chat_data", None) or {}
    lang = chat_data.get("lang", "hi")
    return lang if lang in MSG_LANG_SET else "hi"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_START)


async def bhasha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/bhasha: three buttons, one per language."""
    buttons = [[InlineKeyboardButton(label, callback_data=f"lang:{code}") for label, code in LANGUAGES]]
    await update.message.reply_text(MSG_PICK_LANG, reply_markup=InlineKeyboardMarkup(buttons))


async def on_lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A /bhasha button was pressed: remember the language for this chat and say so."""
    query = update.callback_query
    lang = (query.data or "").partition(":")[2]
    if lang not in MSG_LANG_SET:
        await query.answer()
        return
    context.chat_data["lang"] = lang
    await query.answer()
    await query.edit_message_text(MSG_LANG_SET[lang])


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]  # the largest size
    tg_file = await photo.get_file()
    image = bytes(await tg_file.download_as_bytearray())
    result = await ask_api(update, MSG_BAD_PHOTO,
                           files={"image": ("offer.jpg", image, "image/jpeg")},
                           data={"lang": chat_lang(context), "source": "telegram"})
    if result:
        remember_check(context, result)
        await send_result(update, result)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_data = getattr(context, "chat_data", None)
    if chat_data is not None and chat_data.pop("log_next", False):      # he sent /log before this
        await log_event(update, context, update.message.text or "", update.message.date)
        return
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text(MSG_SEND_PHOTO)
        return
    if len(text) > MAX_TEXT_CHARS:
        await update.message.reply_text(MSG_TOO_LONG)
        return
    result = await ask_api(update, MSG_BAD_TEXT,
                           json={"text": text, "lang": chat_lang(context), "source": "telegram"})
    if result:
        remember_check(context, result)
        await send_result(update, result)


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A voice note (D6): Raju speaks the offer. The API listens (Whisper) and reads it like an SMS."""
    voice = update.message.voice
    if voice is None:
        await update.message.reply_text(MSG_SEND_PHOTO)
        return
    if (voice.duration or 0) > MAX_VOICE_S:
        await update.message.reply_text(MSG_VOICE_TOO_LONG)
        return
    try:
        tg_file = await voice.get_file()
        audio = bytes(await tg_file.download_as_bytearray())
    except Exception as exc:  # Telegram download problem: ask him to send it again
        log.warning("voice download failed: %s", type(exc).__name__)
        await update.message.reply_text(MSG_BAD_VOICE)
        return
    result = await ask_api(update, MSG_BAD_VOICE,
                           files={"audio": ("voice.ogg", audio, voice.mime_type or "audio/ogg")},
                           data={"lang": chat_lang(context), "source": "telegram"})
    if result:
        remember_check(context, result)
        await send_result(update, result)


# ---------------------------------------------------------------- harassment log (D5)
def _iso_ist(when: datetime | None) -> str:
    """Telegram's time (UTC) -> ISO with +05:30, as the API expects. Now if unknown."""
    when = when or datetime.now(timezone.utc)
    when = when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when
    return when.astimezone(IST).isoformat(timespec="seconds")


def remember_check(context, result: dict) -> None:
    """Keep the last check of this chat, so a harassment case links to the lender he checked."""
    chat_data = getattr(context, "chat_data", None)
    if chat_data is not None:
        lender = result.get("lender") or {}
        chat_data["last_check"] = {"id": result.get("id"),
                                   "lender": lender.get("closest") or lender.get("name_read")}


def rules_text(rules: list[str]) -> str:
    """["H1", "H2"] -> the Hindi names, joined."""
    return "; ".join(RULE_HI.get(r, r) for r in rules)


async def _ensure_case(update: Update, context) -> str | None:
    """This chat's case id: created once with POST /api/cases and remembered in chat_data."""
    chat = context.chat_data
    if chat.get("case_id"):
        return chat["case_id"]
    last = chat.get("last_check") or {}
    body = {"borrower_name": "Borrower (Telegram)", "lender_name": last.get("lender") or "Not given"}
    if last.get("id"):
        body["check_id"] = last["id"]
    async with _http(API_TIMEOUT_S) as http:
        r = await http.post(f"{settings.api_url}/api/cases", json=body)
    if r.status_code != 200:
        log.warning("case not created: API answered %s", r.status_code)
        return None
    chat["case_id"] = r.json().get("id")
    return chat["case_id"]


async def send_pdf(update: Update, case_id: str) -> bool:
    """GET the case's evidence PDF and send it as a document. False if it is not available."""
    async with _http(API_TIMEOUT_S) as http:
        r = await http.get(f"{settings.api_url}/api/cases/{case_id}/evidence.pdf")
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        log.warning("evidence PDF not available (%s) for %s", r.status_code, case_id)
        return False
    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    await update.message.reply_document(document=r.content, filename=f"{case_id}_saboot.pdf",
                                        caption=MSG_PDF_CAPTION)
    return True


async def log_event(update: Update, context, text: str, when: datetime | None) -> None:
    """One harassment message -> case event -> Hindi rules line -> evidence PDF."""
    text = (text or "").strip()
    if not text:
        await update.message.reply_text(MSG_LOG_EMPTY)
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    event = {"at": _iso_ist(when), "channel": "telegram", "contacted": "borrower",
             "text": text[:MAX_TEXT_CHARS]}
    try:
        for attempt in (1, 2):                 # a case lost on a server restart is made again once
            case_id = await _ensure_case(update, context)
            if not case_id:
                await update.message.reply_text(MSG_ERROR)
                return
            async with _http(API_TIMEOUT_S) as http:
                r = await http.post(f"{settings.api_url}/api/cases/{case_id}/events", json=event)
            if r.status_code == 404 and attempt == 1:
                context.chat_data.pop("case_id", None)
                continue
            break
        if r.status_code != 200:
            log.warning("event not logged: API answered %s", r.status_code)
            await update.message.reply_text(MSG_ERROR)
            return
        rules = r.json().get("rules") or []
        await update.message.reply_text(MSG_LOGGED.format(rules=rules_text(rules)) if rules
                                        else MSG_LOGGED_NONE)
        if not await send_pdf(update, case_id):
            await update.message.reply_text(MSG_PDF_LATER)
    except httpx.HTTPError:
        log.warning("API not reachable at %s", settings.api_url)
        await update.message.reply_text(MSG_SERVER_DOWN)


async def on_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A forwarded text message = a harassment message to log, at its ORIGINAL time."""
    origin = getattr(update.message, "forward_origin", None)
    when = getattr(origin, "date", None) or update.message.date
    await log_event(update, context, update.message.text or "", when)


async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/log <message> logs it now; /log alone logs the next message he sends."""
    text = " ".join(getattr(context, "args", None) or []).strip()
    if text:
        await log_event(update, context, text, update.message.date)
        return
    context.chat_data["log_next"] = True
    await update.message.reply_text(MSG_LOG_ASK)


async def pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/pdf: the latest evidence PDF of this chat's case again."""
    case_id = context.chat_data.get("case_id")
    if not case_id:
        await update.message.reply_text(MSG_NO_CASE)
        return
    try:
        if not await send_pdf(update, case_id):
            await update.message.reply_text(MSG_PDF_LATER)
    except httpx.HTTPError:
        await update.message.reply_text(MSG_SERVER_DOWN)


async def on_other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MSG_SEND_PHOTO)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """D9: every error is ONE short log line, never a traceback. Polling keeps going on its own.
    A dropped connection or a timeout (TimedOut is a NetworkError) is normal on stage Wi-Fi.
    BadRequest is also a NetworkError in this library, but it is OUR mistake, not the network."""
    err = context.error
    if isinstance(err, NetworkError) and not isinstance(err, BadRequest):
        log.warning("network blip, retrying (%s)", type(err).__name__)
        return
    detail = str(err)
    if settings.telegram_bot_token:
        detail = detail.replace(settings.telegram_bot_token, "<token>")  # never log the key
    log.error("bot error: %s: %s", type(err).__name__, detail[:200])


def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is empty. Put your TEST bot token in .env "
                         "(only the server laptop uses the demo bot token).")
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bhasha", bhasha))
    app.add_handler(CallbackQueryHandler(on_lang_choice, pattern=r"^lang:"))
    app.add_handler(CommandHandler("log", log_command))
    app.add_handler(CommandHandler("pdf", pdf_command))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.TEXT, on_forward))   # before on_text
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(~filters.COMMAND, on_other))
    app.add_error_handler(on_error)          # D9: one line per error, never a traceback
    log.info("Bot is polling. API: %s. Stop with Ctrl+C.", settings.api_url)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
