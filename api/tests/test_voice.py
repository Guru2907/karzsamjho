"""Voice notes (task D6): fallback.transcribe, extract.extract_from_voice and POST /api/checks
with an "audio" field. Fake Whisper, fake text model, fake voice: no test calls the internet."""
import dataclasses
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from api import main
from api.core import config, extract, fallback

SPOKEN = "paanch hazaar ka loan, saat din mein chhe hazaar lautana"
DIGITS = "5000 ka loan, 7 din mein 6000 lautana"
READ_REPLY = {"is_loan_ad": True, "principal": 5000, "repay_total": 6000, "tenure_days": "7 din"}
SENTENCE = ("Aapko haath mein 5000 rupaye milenge. 7 din mein 6000 rupaye "
            "lautane honge. Yaani 1000 rupaye zyada.")
OGG = b"OggS\x00fake voice note"


# ---------------------------------------------------------------- fallback.transcribe
def fake_groq(text="", error=None):
    """A stand-in for groq.Groq that records the client options and the transcription call."""
    calls = []

    class FakeGroq:
        def __init__(self, **kwargs):
            calls.append(("client", kwargs))
            self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self._create))

        def _create(self, **kwargs):
            calls.append(("create", kwargs))
            if error:
                raise error
            return SimpleNamespace(text=text)

    return FakeGroq, calls


@pytest.fixture
def groq_key(monkeypatch):
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(
        fallback.settings, groq_api_key="test-key-not-real", stt_timeout_s=8.0))


def test_transcribe_ok(groq_key, monkeypatch):
    fake, calls = fake_groq(text=f"  {SPOKEN}  ")
    monkeypatch.setattr(fallback, "Groq", fake)
    text, engine, seconds = fallback.transcribe(OGG)
    assert (text, engine) == (SPOKEN, "whisper") and seconds >= 0
    client = calls[0][1]
    assert client["timeout"] == 8.0 and client["max_retries"] == 0      # one try, timeout from config
    create = calls[1][1]
    assert create["file"] == ("voice.ogg", OGG)
    assert create["model"] == fallback.settings.groq_stt_model
    assert create["language"] == "hi" and create["temperature"] == 0


@pytest.mark.parametrize("fake_kwargs", [
    {"error": ConnectionError("no internet")},
    {"error": TimeoutError("too slow")},
    {"text": "   "},                                   # Whisper heard nothing
])
def test_transcribe_failure_is_engine_error(groq_key, monkeypatch, fake_kwargs):
    fake, _ = fake_groq(**fake_kwargs)
    monkeypatch.setattr(fallback, "Groq", fake)
    with pytest.raises(fallback.EngineError):
        fallback.transcribe(OGG)


def test_transcribe_without_key_or_audio_never_calls_groq(monkeypatch):
    fake, calls = fake_groq(text=SPOKEN)
    monkeypatch.setattr(fallback, "Groq", fake)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key=""))
    with pytest.raises(fallback.EngineError):
        fallback.transcribe(OGG)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key="k"))
    with pytest.raises(fallback.EngineError):
        fallback.transcribe(b"")
    assert calls == []


def test_transcribe_never_logs_what_was_said(groq_key, monkeypatch, caplog):
    fake, _ = fake_groq(text=SPOKEN)
    monkeypatch.setattr(fallback, "Groq", fake)
    with caplog.at_level("INFO"):
        fallback.transcribe(OGG)
    assert "paanch" not in caplog.text and "chars=" in caplog.text


# ---------------------------------------------------------------- extract.extract_from_voice
def fake_listen_and_read(monkeypatch, transcript=SPOKEN, digits=DIGITS, reply=READ_REPLY,
                         listen_error=None, digits_error=None):
    """Fake Whisper + fake gpt-oss. The digits rewrite and the field reading are told apart
    by their prompt. Returns the list of text-model prompts, to see what was read."""
    prompts = []

    def transcribe(audio_bytes, lang="hi"):
        if listen_error:
            raise listen_error
        return transcript, "whisper", 0.9

    def read_text(prompt, check=None):
        prompts.append(prompt)
        if prompt.startswith(extract.DIGITS_PROMPT):
            if digits_error:
                raise digits_error
            raw = digits
        else:
            raw = json.dumps(reply)
        if check:
            check(raw)
        return raw, "gpt-oss-20b", 0.7

    monkeypatch.setattr(fallback, "transcribe", transcribe)
    monkeypatch.setattr(fallback, "read_text", read_text)
    return prompts


def test_voice_words_become_digits_then_fields(monkeypatch):
    prompts = fake_listen_and_read(monkeypatch)
    out = extract.extract_from_voice(OGG)
    f = out["fields"]
    assert (f["principal"], f["repay_total"], f["tenure_days"]) == (5000, 6000, 7)
    assert f["fees"] is None and f["in_hand"] is None
    assert out["engines"] == {"read": "gpt-oss-20b", "second_read": None, "listen": "whisper"}
    assert prompts[0] == extract.DIGITS_PROMPT + SPOKEN          # D22: words -> digits first
    assert prompts[1].endswith(DIGITS)                           # then read like an SMS


def test_digits_rewrite_down_uses_the_raw_transcript(monkeypatch):
    raw = "5000 ka loan 7 din mein 6000 lautana"                 # Whisper often writes digits
    prompts = fake_listen_and_read(monkeypatch, transcript=raw,
                                   digits_error=fallback.EngineError("down"))
    out = extract.extract_from_voice(OGG)
    assert out["fields"]["principal"] == 5000 and out["engines"]["listen"] == "whisper"
    assert prompts[-1].endswith(raw)


def test_number_not_in_the_words_is_dropped(monkeypatch):
    # The reader "invents" in_hand 4500; it was never said, so it is dropped (no guessing).
    fake_listen_and_read(monkeypatch, reply={**READ_REPLY, "in_hand": 4500})
    assert extract.extract_from_voice(OGG)["fields"]["in_hand"] is None


@pytest.mark.parametrize("text, expected", [
    ("5000 का लोन, 7 दिन में 6 हजार लोटाना", "5000 का लोन, 7 दिन में 6000 लोटाना"),  # real run, 13 Nov
    ("6 hazaar lautana", "6000 lautana"),
    ("1.5 lakh ka loan", "150000 ka loan"),
    ("१२ सौ फीस", "1200 फीस"),                     # Devanagari digits too
    ("5000 ka loan, 7 din", "5000 ka loan, 7 din"),  # nothing to change
])
def test_expand_multipliers(text, expected):
    assert extract.expand_multipliers(text) == expected


def test_half_converted_rewrite_still_keeps_the_repay(monkeypatch):
    # Real run 13 Nov: Whisper heard "saath" for "saat"; the rewrite left "6 हजार".
    fake_listen_and_read(monkeypatch, transcript="पांच हजार का लोन, साथ दिन में छे हजार लोटाना",
                         digits="5000 का लोन, 7 दिन में 6 हजार लोटाना",
                         reply={"is_loan_ad": True, "principal": 5000, "repay_total": 6000,
                                "tenure_days": "7 दिन"})
    f = extract.extract_from_voice(OGG)["fields"]
    assert (f["principal"], f["repay_total"], f["tenure_days"]) == (5000, 6000, 7)


def test_whisper_down_is_unreadable_with_hindi_text(monkeypatch):
    fake_listen_and_read(monkeypatch, listen_error=fallback.EngineError("down"))
    with pytest.raises(extract.Unreadable) as err:
        extract.extract_from_voice(OGG)
    assert err.value.text_hi == "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."


def test_no_amounts_in_the_voice_note_is_unreadable_voice_message(monkeypatch):
    fake_listen_and_read(monkeypatch, transcript="haan ji namaste", digits="haan ji namaste",
                         reply={"is_loan_ad": True})
    with pytest.raises(extract.Unreadable) as err:
        extract.extract_from_voice(OGG)
    assert err.value.text_hi == extract.MSG_BAD_VOICE


def test_voice_that_is_not_a_loan(monkeypatch):
    fake_listen_and_read(monkeypatch, transcript="aaj sabzi ka bhaav kya hai",
                         digits="aaj sabzi ka bhaav kya hai", reply={"is_loan_ad": False})
    with pytest.raises(extract.NotALoan):
        extract.extract_from_voice(OGG)


# ---------------------------------------------------------------- POST /api/checks with "audio"
@pytest.fixture
def env(monkeypatch, tmp_path):
    """Fresh in-memory store, temp audio + cache folders, fake voice that writes a small MP3."""
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "audio"), cache_dir=str(tmp_path / "cache"),
        voice_enabled=True))
    monkeypatch.setattr(main, "CHECKS", {})
    spoken = []

    async def fake_speak(text, out_path):
        spoken.append(text)
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"\xff\xf3fake-mp3")
        return True

    monkeypatch.setattr(fallback, "speak", fake_speak)
    return SimpleNamespace(spoken=spoken, cache_dir=tmp_path / "cache")


def post_voice(client, data=OGG):
    return client.post("/api/checks", files={"audio": ("voice.ogg", data, "audio/ogg")},
                       data={"lang": "hi", "source": "telegram"})


def test_api_voice_note_end_to_end(client, env, monkeypatch):
    fake_listen_and_read(monkeypatch)
    r = post_voice(client)
    assert r.status_code == 200
    body = r.json()
    numbers = {k: (v["value"], v["status"]) for k, v in body["numbers"].items()}
    # "paanch hazaar ka loan, saat din mein chhe hazaar lautana": no fee said, so in hand = loan.
    assert numbers == {"in_hand": (5000, "derived"), "repay_total": (6000, "read"),
                       "tenure_days": (7, "read"), "extra": (1000, "computed"),
                       "per_day": (143, "computed"), "apr_simple": (1043, "computed")}
    assert body["verdict"] == "VERY_COSTLY"
    assert body["engines"] == {"read": "gpt-oss-20b", "second_read": None,
                               "speak": "edge-tts", "listen": "whisper"}
    assert body["speech_text_hi"] == SENTENCE and env.spoken == [SENTENCE]
    assert client.get(body["audio_url"]).status_code == 200


def test_api_voice_note_is_never_cached(client, env, monkeypatch):
    calls = []
    fake_listen_and_read(monkeypatch)
    real = fallback.transcribe

    def counting(audio_bytes, lang="hi"):
        calls.append(1)
        return real(audio_bytes, lang)

    monkeypatch.setattr(fallback, "transcribe", counting)
    assert post_voice(client).status_code == 200
    assert post_voice(client).status_code == 200
    assert len(calls) == 2                                       # listened to both times
    assert not env.cache_dir.exists() or not any(env.cache_dir.iterdir())


def test_api_whisper_down_is_422_with_hindi_text(client, env, monkeypatch):
    fake_listen_and_read(monkeypatch, listen_error=fallback.EngineError("down"))
    r = post_voice(client)
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "UNREADABLE",
                                  "text_hi": "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."}


def test_api_empty_voice_note_is_422(client, env, monkeypatch):
    fake_listen_and_read(monkeypatch)
    r = post_voice(client, data=b"")
    assert r.status_code == 422 and r.json()["detail"]["code"] == "UNREADABLE"


def test_photo_and_text_checks_have_no_listen(client, env, monkeypatch):
    fake_listen_and_read(monkeypatch)
    r = client.post("/api/checks", json={"text": DIGITS})
    assert r.status_code == 200 and r.json()["engines"]["listen"] is None
