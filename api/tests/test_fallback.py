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
