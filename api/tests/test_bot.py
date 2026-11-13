"""bot/main.py without Telegram or the API: fakes only, no internet."""
import asyncio

import httpx
import pytest

import bot.main as bot

RESULT = {
    "id": "chk_0001",
    "verdict": "VERY_COSTLY",
    "numbers": {"in_hand": {"value": 3800.0, "status": "derived"},
                "repay_total": {"value": 5000.0, "status": "read"},
                "tenure_days": {"value": 7.0, "status": "read"},
                "extra": {"value": 1200.0, "status": "computed"}},
    "lender": {"name_read": "PaisaTurant", "match": None},
    "next_step": {"code": "ASK_BANK_MITRA", "text_hi": "Loan lene se pehle bank mitra se poochho."},
    "audio_url": "/api/audio/chk_0001.mp3",
}


@pytest.mark.parametrize("value, text", [
    (0, "0"), (999, "999"), (3800, "3,800"), (11500, "11,500"), (100000, "1,00,000"),
    (2500000, "25,00,000"), (12345678, "1,23,45,678"), (3799.6, "3,800")])
def test_indian_digits(value, text):
    assert bot.indian_digits(value) == text


def test_rupees():
    assert bot.rupees({"value": 100000, "status": "read"}) == "₹1,00,000"
    assert bot.rupees({"value": 3800, "status": "unverified"}) == "pata nahi chala"
    assert bot.rupees({"value": None, "status": "read"}) == "pata nahi chala"
    assert bot.rupees(None) == "pata nahi chala"


def test_card_very_costly():
    card = bot.card_text(RESULT)
    assert card.splitlines()[0] == "🔴 <b>Bahut mehenga loan</b>"
    assert "<b>₹3,800</b> haath mein" in card
    assert "<b>₹5,000</b> lautana hai" in card
    assert "<b>7 din</b>" in card and "<b>₹1,200 zyada</b>" in card
    assert "RBI" not in card                         # lender not checked tonight -> no line
    assert card.rstrip().endswith("bank mitra se poochho.")


def test_card_cannot_say_never_shows_a_guess():
    numbers = {**RESULT["numbers"], "in_hand": {"value": None, "status": "unverified"},
               "extra": {"value": None, "status": "unverified"}}
    card = bot.card_text({**RESULT, "verdict": "CANNOT_SAY", "numbers": numbers})
    assert "Pakka nahi keh sakte" in card
    assert "<b>pata nahi chala</b> haath mein" in card
    assert "zyada: pata nahi chala" in card


def test_card_escapes_html():
    card = bot.card_text({**RESULT, "next_step": {"code": "X", "text_hi": "<script>bad</script>"}})
    assert "<script>" not in card and "&lt;script&gt;" in card


@pytest.mark.parametrize("match, expected", [
    ("FOUND", "list mein mila: Some NBFC (list: 2026-11-12)"),
    ("SIMILAR", "milta-julta naam hai: Some NBFC"),
    ("NOT_FOUND", "list mein nahi mila (list: 2026-11-12)")])
def test_lender_line_never_says_illegal_or_fake(match, expected):
    line = bot.lender_line({"match": match, "closest": "Some NBFC", "name_read": "X",
                            "list_date": "2026-11-12"})
    assert expected in line
    assert "illegal" not in line.lower() and "fake" not in line.lower()


def test_no_card_text():
    req = httpx.Request("POST", "http://api/api/checks")
    hindi = {"detail": {"code": "NOT_A_LOAN", "text_hi": "Yeh loan ka offer nahi lagta."}}
    assert bot.no_card_text(httpx.Response(422, json=hindi, request=req), "x") == "Yeh loan ka offer nahi lagta."
    assert bot.no_card_text(httpx.Response(422, json={"detail": "old"}, request=req), "fallback") == "fallback"
    assert bot.no_card_text(httpx.Response(500, text="boom", request=req), "fallback") == bot.MSG_ERROR


def test_api_wait_covers_the_worst_photo_check():
    s = bot.settings
    worst = s.vision_timeout_s + 2 * s.read_timeout_s + s.tts_timeout_s
    assert bot.API_TIMEOUT_S > worst                 # 45 s > 36 s with the default timeouts


# ---------------------------------------------------------------- card first, then the MP3
class FakeMessage:
    def __init__(self):
        self.sent = []
        self.chat = self

    async def send_action(self, action):
        pass

    async def reply_text(self, text, parse_mode=None):
        self.sent.append(("text", text))

    async def reply_audio(self, audio, filename, title, performer):
        self.sent.append(("audio", filename, audio))


class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()


def fake_api(monkeypatch, response):
    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url):
            if isinstance(response, Exception):
                raise response
            return response

    monkeypatch.setattr(bot, "_http", Client)


def test_send_result_card_then_mp3(monkeypatch):
    fake_api(monkeypatch, httpx.Response(200, content=b"\xff\xf3mp3"))
    update = FakeUpdate()
    asyncio.run(bot.send_result(update, RESULT))
    assert [m[0] for m in update.message.sent] == ["text", "audio"]
    assert update.message.sent[1][1:] == ("chk_0001.mp3", b"\xff\xf3mp3")


@pytest.mark.parametrize("response", [httpx.Response(404), httpx.ConnectError("down")])
def test_send_result_card_alone_when_audio_fails(monkeypatch, response):
    fake_api(monkeypatch, response)
    update = FakeUpdate()
    asyncio.run(bot.send_result(update, RESULT))
    assert [m[0] for m in update.message.sent] == ["text"]


def test_send_result_no_audio_url(monkeypatch):
    fake_api(monkeypatch, AssertionError("must not fetch"))
    update = FakeUpdate()
    asyncio.run(bot.send_result(update, {**RESULT, "audio_url": None}))
    assert [m[0] for m in update.message.sent] == ["text"]


def test_card_shows_seconds_stamp():
    card = bot.card_text({**RESULT, "seconds": 3.94})
    assert "⏱ <b>3.9 sec</b>" in card
    lines = card.splitlines()
    assert lines.index("⏱ <b>3.9 sec</b>") == lines.index("⚠️ <b>₹1,200 zyada</b>") + 1


@pytest.mark.parametrize("seconds", [None, "fast", True, -1])
def test_card_without_a_usable_seconds_has_no_stamp(seconds):
    assert "⏱" not in bot.card_text({**RESULT, "seconds": seconds})


# ---------------------------------------------------------------- voice notes (D6)
class FakeVoice:
    def __init__(self, duration=8, data=b"OggS fake voice", mime_type="audio/ogg", fail=False):
        self.duration, self.mime_type, self._data, self._fail = duration, mime_type, data, fail

    async def get_file(self):
        if self._fail:
            raise RuntimeError("telegram download failed")
        data = self._data

        class File:
            async def download_as_bytearray(self):
                return bytearray(data)
        return File()


def fake_check_api(monkeypatch, check_response):
    """A fake API: POST /api/checks answers check_response; GET of the MP3 answers audio bytes.
    Returns the list of POST calls (url, kwargs) so a test can see what the bot sent."""
    posts = []

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kwargs):
            posts.append((url, kwargs))
            return check_response

        async def get(self, url):
            return httpx.Response(200, content=b"ID3fake")

    monkeypatch.setattr(bot, "_http", Client)
    return posts


def voice_update(**voice_kwargs):
    update = FakeUpdate()
    update.message.voice = FakeVoice(**voice_kwargs)
    return update


def test_voice_note_is_posted_as_audio_then_card_and_mp3(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    update = voice_update()
    asyncio.run(bot.on_voice(update, None))
    url, kwargs = posts[0]
    assert url.endswith("/api/checks")
    assert kwargs["files"] == {"audio": ("voice.ogg", b"OggS fake voice", "audio/ogg")}
    assert kwargs["data"] == {"lang": "hi", "source": "telegram"}
    assert [s[0] for s in update.message.sent] == ["text", "audio"]     # card, then the MP3


def test_voice_note_longer_than_a_minute_is_refused_in_hindi(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    update = voice_update(duration=61)
    asyncio.run(bot.on_voice(update, None))
    assert posts == []                                                   # Whisper never called
    assert update.message.sent == [("text", bot.MSG_VOICE_TOO_LONG)]


def test_voice_note_of_exactly_a_minute_is_accepted(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    asyncio.run(bot.on_voice(voice_update(duration=60), None))
    assert len(posts) == 1


def test_voice_note_download_failure_is_a_hindi_message(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    update = voice_update(fail=True)
    asyncio.run(bot.on_voice(update, None))
    assert posts == [] and update.message.sent == [("text", bot.MSG_BAD_VOICE)]


def test_voice_note_unclear_shows_the_api_hindi_text(monkeypatch):
    detail = {"code": "UNREADABLE", "text_hi": "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."}
    fake_check_api(monkeypatch, httpx.Response(422, json={"detail": detail}))
    update = voice_update()
    asyncio.run(bot.on_voice(update, None))
    assert update.message.sent == [("text", detail["text_hi"])]


def test_voice_note_without_mime_type_is_sent_as_ogg(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    asyncio.run(bot.on_voice(voice_update(mime_type=None), None))
    assert posts[0][1]["files"]["audio"][2] == "audio/ogg"


# ---------------------------------------------------------------- /bhasha (D7)
from types import SimpleNamespace  # noqa: E402


class MarkupMessage(FakeMessage):
    async def reply_text(self, text, parse_mode=None, reply_markup=None):
        self.sent.append(("text", text, reply_markup))


class FakeQuery:
    def __init__(self, data):
        self.data, self.answered, self.edited = data, False, None

    async def answer(self):
        self.answered = True

    async def edit_message_text(self, text):
        self.edited = text


def test_bhasha_shows_three_language_buttons():
    update = FakeUpdate()
    update.message = MarkupMessage()
    asyncio.run(bot.bhasha(update, SimpleNamespace(chat_data={})))
    _, text, markup = update.message.sent[0]
    assert text == bot.MSG_PICK_LANG
    buttons = markup.inline_keyboard[0]
    assert [(b.text, b.callback_data) for b in buttons] == [
        ("Hindi", "lang:hi"), ("বাংলা", "lang:bn"), ("मराठी", "lang:mr")]


@pytest.mark.parametrize("lang", ["hi", "bn", "mr"])
def test_pressing_a_button_remembers_the_language(lang):
    context = SimpleNamespace(chat_data={})
    query = FakeQuery(f"lang:{lang}")
    asyncio.run(bot.on_lang_choice(SimpleNamespace(callback_query=query), context))
    assert context.chat_data == {"lang": lang}
    assert query.answered and query.edited == bot.MSG_LANG_SET[lang]


def test_unknown_button_data_changes_nothing():
    context = SimpleNamespace(chat_data={"lang": "bn"})
    query = FakeQuery("lang:kn")
    asyncio.run(bot.on_lang_choice(SimpleNamespace(callback_query=query), context))
    assert context.chat_data == {"lang": "bn"} and query.answered and query.edited is None


@pytest.mark.parametrize("context, expected", [
    (None, "hi"), (SimpleNamespace(chat_data={}), "hi"), (SimpleNamespace(chat_data={"lang": "mr"}), "mr"),
    (SimpleNamespace(chat_data={"lang": "xx"}), "hi")])
def test_chat_lang(context, expected):
    assert bot.chat_lang(context) == expected


def test_chosen_language_is_sent_with_photo_text_and_voice(monkeypatch):
    posts = fake_check_api(monkeypatch, httpx.Response(200, json=RESULT))
    context = SimpleNamespace(chat_data={"lang": "bn"})

    photo_update = FakeUpdate()
    photo_update.message.photo = [FakeVoice(data=b"\xff\xd8 jpeg")]      # same get_file shape
    asyncio.run(bot.on_photo(photo_update, context))

    text_update = FakeUpdate()
    text_update.message.text = "Loan Rs 5000. Repay Rs 5600 in 7 days."
    asyncio.run(bot.on_text(text_update, context))

    asyncio.run(bot.on_voice(voice_update(), context))

    assert posts[0][1]["data"]["lang"] == "bn"                 # photo
    assert posts[1][1]["json"]["lang"] == "bn"                 # pasted SMS
    assert posts[2][1]["data"]["lang"] == "bn"                 # voice note


def test_card_text_stays_hinglish_whatever_the_language():
    assert "haath mein" in bot.card_text(RESULT) and "lautana hai" in bot.card_text(RESULT)


# ---------------------------------------------------------------- harassment log (D5)
from datetime import datetime as _dt, timezone as _tz  # noqa: E402

from api.core import evidence  # noqa: E402

ORIGINAL_TIME = _dt(2026, 11, 13, 16, 10, tzinfo=_tz.utc)            # = 9:40 PM IST
THREAT = "Paisa do warna ghar aa jayenge."


class LogMessage(FakeMessage):
    """A Telegram message that can be forwarded and can receive a document."""
    def __init__(self, text=THREAT, forwarded=True):
        super().__init__()
        self.text, self.caption = text, None
        self.date = _dt(2026, 11, 13, 18, 0, tzinfo=_tz.utc)          # when it reached the bot
        self.forward_origin = SimpleNamespace(date=ORIGINAL_TIME) if forwarded else None

    async def reply_document(self, document, filename=None, caption=None):
        self.sent.append(("document", filename, document[:4], caption))


def log_update(**kwargs):
    update = FakeUpdate()
    update.message = LogMessage(**kwargs)
    return update


def fake_cases_api(monkeypatch, rules=("H1", "H2"), event_status=200, pdf_status=200,
                   case_lost_once=False, down=False):
    """A fake API for /api/cases. The PDF it serves is the REAL F3 evidence PDF."""
    calls = []
    state = {"lost": case_lost_once, "cases": 0}

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, **kwargs):
            calls.append(("POST", url.split("/api", 1)[1], json))
            if down:
                raise httpx.ConnectError("refused")
            if url.endswith("/api/cases"):
                state["cases"] += 1
                case_id = "case_000" + str(state["cases"])
                return httpx.Response(200, json={"id": case_id, "borrower_name": "x",
                                                 "lender_name": "x", "opened_at": "x", "events": []})
            if state["lost"]:
                state["lost"] = False
                return httpx.Response(404, json={"detail": "Case not found."})
            return httpx.Response(event_status, json={"id": "evt_0001", "at": json["at"],
                                                      "rules": list(rules), "hash": "a" * 64,
                                                      "prev_hash": "0" * 64})

        async def get(self, url):
            calls.append(("GET", url.split("/api", 1)[1], None))
            if pdf_status != 200:
                return httpx.Response(pdf_status, json={"detail": "No PDF yet."})
            return httpx.Response(200, content=evidence.build_pdf({"id": "case_0001", "events": []}))

    monkeypatch.setattr(bot, "_http", Client)
    return calls


def test_forwarded_threat_becomes_event_then_rules_then_pdf(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    context = SimpleNamespace(chat_data={})
    update = log_update()
    asyncio.run(bot.on_forward(update, context))
    assert calls[0][:2] == ("POST", "/cases")
    assert calls[1] == ("POST", "/cases/case_0001/events",
                        {"at": "2026-11-13T21:40:00+05:30", "channel": "telegram",
                         "contacted": "borrower", "text": THREAT})     # the ORIGINAL time, in IST
    assert calls[2] == ("GET", "/cases/case_0001/evidence.pdf", None)
    kind, text = update.message.sent[0]
    assert kind == "text" and text.startswith("Darj ho gaya.")
    assert "H1 raat" in text and "H2 dhamki" in text
    doc = update.message.sent[1]
    assert doc[0] == "document" and doc[1] == "case_0001_saboot.pdf" and doc[2] == b"%PDF"
    assert context.chat_data["case_id"] == "case_0001"


def test_case_is_created_once_per_chat(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    context = SimpleNamespace(chat_data={})
    asyncio.run(bot.on_forward(log_update(), context))
    asyncio.run(bot.on_forward(log_update(text="Kal phir call karenge."), context))
    assert [c[1] for c in calls if c[0] == "POST"].count("/cases") == 1


def test_case_names_the_lender_he_checked(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    context = SimpleNamespace(chat_data={})
    bot.remember_check(context, {"id": "chk_0009", "lender": {"name_read": "QuickCash", "closest": None}})
    asyncio.run(bot.on_forward(log_update(), context))
    assert calls[0][2] == {"borrower_name": "Borrower (Telegram)", "lender_name": "QuickCash",
                           "check_id": "chk_0009"}


def test_log_then_next_message_is_logged_not_checked(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    context = SimpleNamespace(chat_data={}, args=[])
    first = log_update(forwarded=False)
    asyncio.run(bot.log_command(first, context))
    assert first.message.sent == [("text", bot.MSG_LOG_ASK)] and context.chat_data["log_next"]
    second = log_update(text="Tumhare office mein sabko bata denge.", forwarded=False)
    asyncio.run(bot.on_text(second, context))
    assert not any(c[1] == "/checks" for c in calls)                   # not treated as a loan offer
    assert calls[1][2]["text"] == "Tumhare office mein sabko bata denge."
    assert calls[1][2]["at"] == "2026-11-13T23:30:00+05:30"            # its own time (18:00 UTC)
    assert "log_next" not in context.chat_data


def test_log_with_words_logs_them_at_once(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    context = SimpleNamespace(chat_data={}, args=["Police", "bhejenge"])
    asyncio.run(bot.log_command(log_update(forwarded=False), context))
    assert calls[1][2]["text"] == "Police bhejenge"


def test_no_rules_broken_is_still_logged(monkeypatch):
    fake_cases_api(monkeypatch, rules=())
    update = log_update(text="Namaste, EMI kal due hai.")
    asyncio.run(bot.on_forward(update, SimpleNamespace(chat_data={})))
    assert update.message.sent[0] == ("text", bot.MSG_LOGGED_NONE)


def test_pdf_not_ready_says_so_in_hindi(monkeypatch):
    fake_cases_api(monkeypatch, pdf_status=404)
    update = log_update()
    asyncio.run(bot.on_forward(update, SimpleNamespace(chat_data={})))
    assert update.message.sent[-1] == ("text", bot.MSG_PDF_LATER)


def test_case_lost_on_a_server_restart_is_made_again_once(monkeypatch):
    calls = fake_cases_api(monkeypatch, case_lost_once=True)
    context = SimpleNamespace(chat_data={"case_id": "case_0099"})
    update = log_update()
    asyncio.run(bot.on_forward(update, context))
    posts = [c[1] for c in calls if c[0] == "POST"]
    assert posts == ["/cases/case_0099/events", "/cases", "/cases/case_0001/events"]
    assert context.chat_data["case_id"] == "case_0001" and update.message.sent[1][0] == "document"


def test_server_down_while_logging(monkeypatch):
    fake_cases_api(monkeypatch, down=True)
    update = log_update()
    asyncio.run(bot.on_forward(update, SimpleNamespace(chat_data={})))
    assert update.message.sent == [("text", bot.MSG_SERVER_DOWN)]


def test_empty_forward_is_not_logged(monkeypatch):
    calls = fake_cases_api(monkeypatch)
    update = log_update(text="   ")
    asyncio.run(bot.on_forward(update, SimpleNamespace(chat_data={})))
    assert calls == [] and update.message.sent == [("text", bot.MSG_LOG_EMPTY)]


def test_pdf_command(monkeypatch):
    fake_cases_api(monkeypatch)
    none = log_update(forwarded=False)
    asyncio.run(bot.pdf_command(none, SimpleNamespace(chat_data={})))
    assert none.message.sent == [("text", bot.MSG_NO_CASE)]
    has_case = log_update(forwarded=False)
    asyncio.run(bot.pdf_command(has_case, SimpleNamespace(chat_data={"case_id": "case_0001"})))
    assert has_case.message.sent[0][0] == "document"


def test_log_messages_are_hindi_never_error_codes():
    for msg in (bot.MSG_LOG_ASK, bot.MSG_LOGGED_NONE, bot.MSG_PDF_LATER, bot.MSG_NO_CASE, bot.MSG_LOG_EMPTY):
        assert "error" not in msg.lower() and "404" not in msg
    assert set(bot.RULE_HI) == {"H1", "H2", "H3", "H4", "H5", "H6"}
