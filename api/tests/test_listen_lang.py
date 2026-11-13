"""D8: voice notes in Bengali and Marathi (the /bhasha language reaches the listener). No internet."""
import dataclasses
import json
from types import SimpleNamespace

import pytest

from api.core import extract, fallback

OGG = b"OggS fake voice note"
# The real Gemini listener, taken when this file loads (conftest swaps in an offline stand-in per test).
_REAL_GEMINI_AUDIO = fallback._call_gemini_audio


@pytest.mark.parametrize("lang, expected", [("hi", "hi"), ("bn", "bn"), ("mr", "mr"), ("xx", "hi")])
def test_whisper_is_told_the_language(monkeypatch, lang, expected):
    calls = []

    class FakeGroq:
        def __init__(self, **kwargs):
            self.audio = SimpleNamespace(transcriptions=SimpleNamespace(create=self.create))

        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text="5000")
    monkeypatch.setattr(fallback, "Groq", FakeGroq)
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key="test-not-real"))
    assert fallback.transcribe(OGG, lang)[:2] == ("5000", "whisper")
    assert calls[0]["language"] == expected and calls[0]["temperature"] == 0


@pytest.mark.parametrize("lang, word", [("hi", "Hindi"), ("bn", "Bengali"), ("mr", "Marathi")])
def test_gemini_backup_prompt_names_the_language(monkeypatch, lang, word):
    seen = {}

    class Models:
        def generate_content(self, **kwargs):
            seen["prompt"] = kwargs["contents"][1]
            return SimpleNamespace(text="৫০০০ টাকা")
    monkeypatch.setattr(fallback, "_gemini_client", lambda timeout: SimpleNamespace(models=Models()))
    assert _REAL_GEMINI_AUDIO(OGG, lang) == "৫০০০ টাকা"
    assert f"speaking {word}" in seen["prompt"]


def test_transcribe_passes_lang_to_the_gemini_backup_too(monkeypatch):
    got = []
    monkeypatch.setattr(fallback, "_call_whisper", lambda audio, lang="hi": (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setattr(fallback, "_call_gemini_audio", lambda audio, lang="hi": got.append(lang) or "5000")
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(
        fallback.settings, groq_api_key="test-not-real", gemini_api_key="test-not-real"))
    assert fallback.transcribe(OGG, "mr")[1] == "gemini" and got == ["mr"]


@pytest.mark.parametrize("raw, expected", [
    ("৬ হাজার টাকা", "6000 টাকা"),                  # Bengali digits + হাজার
    ("৫০০০ টাকার লোন", "5000 টাকার লোন"),
    ("12 শো টাকা ফেরত", "1200 টাকা ফেরত"),
    ("1.5 লাখ", "150000"),
    ("6 हजार रुपये परत", "6000 रुपये परत"),          # Marathi uses हजार too
    ("12 शे रुपये", "1200 रुपये"),
    ("5 शेकडा", "5 शेकडा"),                          # never inside a longer word ("per hundred")
    ("6 hazaar", "6000"),                            # Hindi unchanged
])
def test_expand_multipliers_bn_mr(raw, expected):
    assert extract.expand_multipliers(raw) == expected


def test_digits_prompt_has_bengali_and_marathi_examples():
    assert '"পাঁচ হাজার" -> 5000' in extract.DIGITS_PROMPT
    assert '"पाच हजार" -> 5000' in extract.DIGITS_PROMPT


@pytest.mark.parametrize("lang, transcript, digits", [
    ("bn", "পাঁচ হাজার টাকার লোন, সাত দিনে ছয় হাজার টাকা ফেরত দিতে হবে",
     "5000 টাকার লোন, 7 দিনে 6000 টাকা ফেরত দিতে হবে"),
    ("mr", "पाच हजार रुपयांचे कर्ज, सात दिवसांत सहा हजार रुपये परत करावे लागतील",
     "5000 रुपयांचे कर्ज, 7 दिवसांत 6000 रुपये परत करावे लागतील"),
])
def test_voice_note_in_bn_mr_gives_the_numbers(monkeypatch, lang, transcript, digits):
    heard = []

    def transcribe(audio_bytes, lang="hi"):
        heard.append(lang)
        return transcript, "whisper", 0.9

    def read_text(prompt, check=None):
        raw = digits if prompt.startswith(extract.DIGITS_PROMPT) else json.dumps(
            {"is_loan_ad": True, "principal": 5000, "repay_total": 6000, "tenure_days": 7})
        if check:
            check(raw)
        return raw, "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "transcribe", transcribe)
    monkeypatch.setattr(fallback, "read_text", read_text)
    out = extract.extract_from_voice(OGG, lang)
    f = out["fields"]
    assert heard == [lang] and out["engines"]["listen"] == "whisper"
    assert (f["principal"], f["repay_total"], f["tenure_days"]) == (5000, 6000, 7)


def test_api_passes_the_form_lang_to_the_listener(client, monkeypatch, tmp_path):
    from api import main
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})
    heard = []

    def extract_from_voice(audio_bytes, lang="hi"):
        heard.append(lang)
        return {"fields": {**{k: None for k in extract.FIELD_KEYS}, "is_loan_ad": True, "principal": 5000,
                           "repay_total": 6000, "tenure_days": 7},
                "engines": {"read": "gpt-oss-20b", "second_read": None, "listen": "whisper"}}
    monkeypatch.setattr(extract, "extract_from_voice", extract_from_voice)
    r = client.post("/api/checks", files={"audio": ("voice.ogg", OGG, "audio/ogg")},
                    data={"lang": "mr", "source": "test"})
    assert r.status_code == 200 and heard == ["mr"]
    assert r.json()["numbers"]["extra"]["value"] == 1000
