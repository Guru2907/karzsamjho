"""fallback.speak with a fake edge-tts: no test calls the internet."""
import asyncio
import dataclasses

from api.core import fallback

SENTENCE = ("Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye "
            "lautane honge. Yaani 1200 rupaye zyada.")


def fake_tts(audio: bytes = b"ID3fake-mp3", delay: float = 0.0, error: Exception | None = None):
    """A stand-in for edge_tts.Communicate that records what it was asked to say."""
    calls = []

    class FakeCommunicate:
        def __init__(self, text, voice):
            calls.append((text, voice))

        async def save(self, path):
            if delay:
                await asyncio.sleep(delay)
            if error:
                raise error
            with open(path, "wb") as f:
                f.write(audio)

    return FakeCommunicate, calls


def test_speak_writes_mp3_with_the_hindi_voice(tmp_path, monkeypatch):
    fake, calls = fake_tts()
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    out = tmp_path / "audio" / "chk_0001.mp3"          # folder does not exist yet
    assert asyncio.run(fallback.speak(SENTENCE, str(out))) is True
    assert out.read_bytes() == b"ID3fake-mp3"
    assert calls == [(SENTENCE, "hi-IN-SwaraNeural")]
    assert not (tmp_path / "audio" / "chk_0001.mp3.part").exists()


def test_speak_failure_returns_false_and_leaves_no_file(tmp_path, monkeypatch):
    fake, _ = fake_tts(error=ConnectionError("no internet"))
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    out = tmp_path / "chk_0002.mp3"
    assert asyncio.run(fallback.speak(SENTENCE, str(out))) is False
    assert list(tmp_path.iterdir()) == []


def test_speak_timeout_returns_false(tmp_path, monkeypatch):
    fake, _ = fake_tts(delay=1.0)
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    monkeypatch.setattr(fallback, "settings",
                        dataclasses.replace(fallback.settings, tts_timeout_s=0.05))
    out = tmp_path / "chk_0003.mp3"
    assert asyncio.run(fallback.speak(SENTENCE, str(out))) is False
    assert not out.exists()


def test_speak_empty_audio_returns_false(tmp_path, monkeypatch):
    fake, _ = fake_tts(audio=b"")
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    out = tmp_path / "chk_0004.mp3"
    assert asyncio.run(fallback.speak(SENTENCE, str(out))) is False
    assert list(tmp_path.iterdir()) == []


def test_speak_empty_text_never_calls_edge_tts(tmp_path, monkeypatch):
    fake, calls = fake_tts()
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    assert asyncio.run(fallback.speak("   ", str(tmp_path / "x.mp3"))) is False
    assert calls == []


# ---------------------------------------------------------------- read_image / read_text
import json  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from groq import RateLimitError  # noqa: E402

GOOD = '{"is_loan_ad": true, "principal": 5000}'
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 20


@pytest.fixture(autouse=True)
def fake_keys(monkeypatch):
    """CI has no .env, so give every test fake keys (the fakes never send them anywhere)."""
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(
        fallback.settings, groq_api_key="fake-groq", gemini_api_key="fake-gemini"))


def rate_limited():
    resp = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com/x"))
    return RateLimitError("rate limit", response=resp, body=None)


def engines(monkeypatch, qwen=None, gemini=None):
    """Replace both photo readers. Each is a reply string or an exception to raise."""
    calls = []

    def make(name, outcome):
        def call(image_bytes, prompt):
            calls.append(name)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome, {"prompt_tokens": 2500, "completion_tokens": 60}
        return call

    monkeypatch.setattr(fallback, "_call_qwen", make("qwen", qwen))
    monkeypatch.setattr(fallback, "_call_gemini", make("gemini", gemini))
    return calls


def test_read_image_qwen_first(monkeypatch):
    calls = engines(monkeypatch, qwen=GOOD, gemini=GOOD)
    raw, engine, seconds = fallback.read_image(PNG, "read this")
    assert (raw, engine) == (GOOD, "qwen") and seconds >= 0
    assert calls == ["qwen"]                       # Gemini never called


def test_read_image_groq_429_goes_to_gemini_at_once(monkeypatch):
    calls = engines(monkeypatch, qwen=rate_limited(), gemini=GOOD)
    raw, engine, _ = fallback.read_image(PNG, "read this")
    assert engine == "gemini" and calls == ["qwen", "gemini"]   # no retry on Qwen


def test_read_image_invalid_json_counts_as_failure(monkeypatch):
    calls = engines(monkeypatch, qwen="sorry, cannot read", gemini=GOOD)
    raw, engine, _ = fallback.read_image(PNG, "read this", check=json.loads)
    assert engine == "gemini" and calls == ["qwen", "gemini"]


def test_read_image_all_fail_raises_engine_error(monkeypatch):
    engines(monkeypatch, qwen=TimeoutError(), gemini=ConnectionError())
    with pytest.raises(fallback.EngineError):
        fallback.read_image(PNG, "read this")


def test_read_image_only_the_other_reader(monkeypatch):
    calls = engines(monkeypatch, qwen=GOOD, gemini=GOOD)
    _, engine, _ = fallback.read_image(PNG, "read this", engines=("gemini",))
    assert engine == "gemini" and calls == ["gemini"]   # used by the second reading


def test_read_image_skips_an_engine_with_no_key(monkeypatch):
    calls = engines(monkeypatch, qwen=GOOD, gemini=GOOD)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key=""))
    _, engine, _ = fallback.read_image(PNG, "read this")
    assert engine == "gemini" and calls == ["gemini"]


def test_qwen_call_uses_temperature_0_no_retries_and_logs_tokens(monkeypatch, caplog):
    seen = {}

    class Raw:
        headers = {"x-ratelimit-remaining-tokens": "7400"}

        def parse(self):
            usage = type("U", (), {"prompt_tokens": 2480, "completion_tokens": 55})
            msg = type("M", (), {"content": "<think>hmm</think>```json\n" + GOOD + "\n```"})
            choice = type("C", (), {"message": msg})
            return type("R", (), {"usage": usage, "choices": [choice]})

    class FakeGroq:
        def __init__(self, api_key, timeout, max_retries):
            seen.update(timeout=timeout, max_retries=max_retries)
            create = lambda **kw: (seen.update(kw), Raw())[1]  # noqa: E731
            raw_resp = type("WR", (), {"create": staticmethod(create)})
            self.chat = type("Ch", (), {"completions": type("Co", (), {"with_raw_response": raw_resp})})

    monkeypatch.setattr(fallback, "Groq", FakeGroq)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key="test"))
    caplog.set_level("INFO", logger="fallback")
    raw, engine, _ = fallback.read_image(PNG, "read this", engines=("qwen",))
    assert engine == "qwen" and "<think>" not in raw and GOOD in raw
    assert seen["temperature"] == 0 and seen["max_retries"] == 0 and seen["timeout"] == 6
    image_part = seen["messages"][0]["content"][1]["image_url"]["url"]
    assert image_part.startswith("data:image/png;base64,")
    assert "prompt_tokens=2480" in caplog.text and "remaining_tokens=7400" in caplog.text
    assert "test" not in caplog.text.replace("tests", "")       # the key is never logged


def test_read_text_ok_and_failure(monkeypatch):
    monkeypatch.setattr(fallback, "_call_gpt_oss", lambda prompt: (GOOD, {}))
    assert fallback.read_text("loan 5000")[:2] == (GOOD, "gpt-oss-20b")
    monkeypatch.setattr(fallback, "_call_gpt_oss", lambda prompt: (_ for _ in ()).throw(rate_limited()))
    with pytest.raises(fallback.EngineError):
        fallback.read_text("loan 5000")
    monkeypatch.setattr(fallback, "_call_gpt_oss", lambda prompt: ("not json", {}))
    with pytest.raises(fallback.EngineError):
        fallback.read_text("loan 5000", check=json.loads)


# ---------------------------------------------------------------- B11: Gemini backup for text and voice
def text_engines(monkeypatch, gpt=None, gemini=None):
    calls = []

    def make(name, outcome):
        def call(prompt):
            calls.append(name)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome, {}
        return call
    monkeypatch.setattr(fallback, "_call_gpt_oss", make("gpt-oss-20b", gpt))
    monkeypatch.setattr(fallback, "_call_gemini_text", make("gemini", gemini))
    return calls


def test_read_text_groq_429_goes_to_gemini_at_once(monkeypatch):
    calls = text_engines(monkeypatch, gpt=rate_limited(), gemini=GOOD)
    raw, engine, _ = fallback.read_text("loan 5000")
    assert (raw, engine) == (GOOD, "gemini") and calls == ["gpt-oss-20b", "gemini"]


def test_read_text_gpt_ok_gemini_never_called(monkeypatch):
    calls = text_engines(monkeypatch, gpt=GOOD, gemini=GOOD)
    assert fallback.read_text("loan 5000")[1] == "gpt-oss-20b" and calls == ["gpt-oss-20b"]


def test_read_text_bad_json_from_gpt_moves_to_gemini(monkeypatch):
    calls = text_engines(monkeypatch, gpt="not json", gemini=GOOD)
    assert fallback.read_text("loan 5000", check=json.loads)[1] == "gemini"
    assert calls == ["gpt-oss-20b", "gemini"]


def test_read_text_both_fail_raises_for_the_regex_backup(monkeypatch):
    text_engines(monkeypatch, gpt=TimeoutError(), gemini=ConnectionError())
    with pytest.raises(fallback.EngineError):
        fallback.read_text("loan 5000")


def test_read_text_without_groq_key_uses_gemini(monkeypatch):
    calls = text_engines(monkeypatch, gpt=GOOD, gemini=GOOD)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key=""))
    assert fallback.read_text("loan 5000")[1] == "gemini" and calls == ["gemini"]


def listeners(monkeypatch, whisper=None, gemini=None):
    calls = []

    def make(name, outcome):
        def call(audio_bytes, lang="hi"):
            calls.append(name)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        return call
    monkeypatch.setattr(fallback, "_call_whisper", make("whisper", whisper))
    monkeypatch.setattr(fallback, "_call_gemini_audio", make("gemini", gemini))
    return calls


def test_transcribe_whisper_first(monkeypatch):
    calls = listeners(monkeypatch, whisper="paanch hazaar ka loan", gemini="x")
    assert fallback.transcribe(b"OggS...")[:2] == ("paanch hazaar ka loan", "whisper") and calls == ["whisper"]


def test_transcribe_whisper_down_gemini_listens(monkeypatch):
    calls = listeners(monkeypatch, whisper=rate_limited(), gemini="5000 ka loan hai 7 din mein 6000 lautana hai")
    text, engine, _ = fallback.transcribe(b"OggS...")
    assert engine == "gemini" and "5000" in text and calls == ["whisper", "gemini"]


def test_transcribe_empty_whisper_text_moves_on(monkeypatch):
    calls = listeners(monkeypatch, whisper="", gemini="das hazaar")
    assert fallback.transcribe(b"OggS...")[1] == "gemini" and calls == ["whisper", "gemini"]


def test_transcribe_both_down(monkeypatch):
    listeners(monkeypatch, whisper=TimeoutError(), gemini=ConnectionError())
    with pytest.raises(fallback.EngineError):
        fallback.transcribe(b"OggS...")
    with pytest.raises(fallback.EngineError):
        fallback.transcribe(b"")                                   # empty audio never calls anyone


@pytest.mark.parametrize("head, mime", [(b"OggS\x00\x02", "audio/ogg"), (b"RIFF\x00\x00\x00\x00WAVE", "audio/wav"),
                                        (b"ID3\x04", "audio/mpeg")])
def test_audio_mime(head, mime):
    assert fallback._audio_mime(head) == mime


def test_sms_end_to_end_reads_through_gemini_when_groq_is_down(monkeypatch):
    from api.core import extract
    text_engines(monkeypatch, gpt=rate_limited(), gemini=json.dumps(
        {"is_loan_ad": True, "principal": 5000, "fees": 500, "repay_total": 5600, "tenure_days": "7 days"}))
    result = extract.extract_from_text("Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days.")
    assert result["engines"]["read"] == "gemini" and result["fields"]["repay_total"] == 5600


# The real Gemini functions, taken when this file loads (before conftest swaps in offline stand-ins).
_REAL_GEMINI_TEXT = fallback._call_gemini_text
_REAL_GEMINI_AUDIO = fallback._call_gemini_audio


@pytest.mark.parametrize("call, arg", [(_REAL_GEMINI_TEXT, "Say OK"), (_REAL_GEMINI_AUDIO, b"OggS...")])
def test_gemini_client_is_kept_alive_during_the_call(monkeypatch, call, arg):
    # Regression (12:40 AM drill): a Gemini client not kept in a variable is closed by Python before
    # the request is sent ("client has been closed"). This fake fails the same way if the code drops it.
    state = {"closed": False}

    class Models:
        def generate_content(self, **kwargs):
            if state["closed"]:
                raise RuntimeError("Cannot send a request, as the client has been closed.")
            return type("R", (), {"text": "OK", "usage_metadata": None})()

    class FakeClient:
        def __init__(self, **kwargs):
            state["closed"] = False
            self.models = Models()

        def __del__(self):
            state["closed"] = True

    monkeypatch.setattr(fallback.genai, "Client", FakeClient)
    result = call(arg)
    assert (result[0] if isinstance(result, tuple) else result) == "OK"
