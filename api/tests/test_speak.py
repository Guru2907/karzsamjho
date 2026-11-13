"""Tests for the Hindi sentence and the MP3 (task D2). Expected values: docs/PLAN.md
("Speech" and "Audio"). fallback.speak is replaced by a fake: no test calls the internet."""
import asyncio
import dataclasses

import pytest

from api.core import config, fallback
from api.core.speak import NOT_CLEAR, make_audio, speech_text

U = {"value": None, "status": "unverified"}

ROW1 = {"in_hand": {"value": 3800, "status": "derived"},
        "repay_total": {"value": 5000, "status": "read"},
        "tenure_days": {"value": 7, "status": "read"},
        "extra": {"value": 1200, "status": "computed"},
        "per_day": {"value": 171, "status": "computed"},
        "apr_simple": {"value": 1647, "status": "computed"}}
ROW8 = {**ROW1, "tenure_days": U, "per_day": U, "apr_simple": U}   # days missing


# --- the sentence ---

def test_row1_sentence_exact():
    assert speech_text(ROW1) == ("Aapko haath mein 3800 rupaye milenge. "
                                 "7 din mein 5000 rupaye lautane honge. "
                                 "Yaani 1200 rupaye zyada.")


def test_row8_days_missing_says_not_clear():
    assert speech_text(ROW8) == ("Is offer ke saare number saaf nahi padhe gaye. "
                                 "Loan lene se pehle bank mitra se poochho.")


@pytest.mark.parametrize("key", ["in_hand", "repay_total", "tenure_days", "extra"])
def test_any_needed_number_unverified_says_not_clear(key):
    assert speech_text({**ROW1, key: U}) == NOT_CLEAR


def test_whole_numbers_without_commas():
    big = {**ROW1, "in_hand": {"value": 12500.0, "status": "read"},
           "repay_total": {"value": 15000.4, "status": "read"},
           "extra": {"value": 2500, "status": "computed"}}
    text = speech_text(big)
    assert "haath mein 12500 rupaye" in text and "15000 rupaye lautane" in text
    assert "," not in text and ".0" not in text


def test_empty_numbers_do_not_crash():
    assert speech_text({}) == NOT_CLEAR


# --- the MP3 (fake fallback.speak) ---

@pytest.fixture
def audio_dir(tmp_path, monkeypatch):
    """Write MP3s to a temporary folder, with voice switched on."""
    monkeypatch.setattr(config, "settings",
                        dataclasses.replace(config.settings, audio_dir=str(tmp_path), voice_enabled=True))
    return tmp_path


def fake_speak(works: bool):
    calls = []

    async def speak(text: str, out_path: str) -> bool:
        calls.append((text, out_path))
        if works:
            with open(out_path, "wb") as f:
                f.write(b"ID3 fake mp3")
        return works
    return speak, calls


def test_audio_ok_returns_url(audio_dir, monkeypatch):
    speak, calls = fake_speak(works=True)
    monkeypatch.setattr(fallback, "speak", speak)
    url = asyncio.run(make_audio("chk_0001", speech_text(ROW1)))
    assert url == "/api/audio/chk_0001.mp3"
    assert (audio_dir / "chk_0001.mp3").exists()
    assert calls == [(speech_text(ROW1), str(audio_dir / "chk_0001.mp3"))]


def test_audio_failed_returns_none(audio_dir, monkeypatch):
    speak, _ = fake_speak(works=False)
    monkeypatch.setattr(fallback, "speak", speak)
    assert asyncio.run(make_audio("chk_0001", speech_text(ROW1))) is None


def test_audio_error_returns_none_not_a_crash(audio_dir, monkeypatch):
    async def broken(text, out_path):
        raise RuntimeError("edge-tts down")
    monkeypatch.setattr(fallback, "speak", broken)
    assert asyncio.run(make_audio("chk_0001", speech_text(ROW1))) is None


def test_voice_switched_off_returns_none_without_calling_speak(audio_dir, monkeypatch):
    speak, calls = fake_speak(works=True)
    monkeypatch.setattr(fallback, "speak", speak)
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, voice_enabled=False))
    assert asyncio.run(make_audio("chk_0001", speech_text(ROW1))) is None
    assert calls == []


def test_unsafe_check_id_is_refused(audio_dir, monkeypatch):
    speak, calls = fake_speak(works=True)
    monkeypatch.setattr(fallback, "speak", speak)
    assert asyncio.run(make_audio("../../evil", "text")) is None
    assert calls == []
