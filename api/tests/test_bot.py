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
