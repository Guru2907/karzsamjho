"""Bengali and Marathi voice (task D7, D32, D35). Expected sentences are copied from docs/PLAN.md.
Fake readers and a fake edge-tts: no test calls the internet."""
import asyncio
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

from api import main
from api.core import cache, config, fallback
from api.core.speak import make_audio, speech_text

U = {"value": None, "status": "unverified"}
ROW1 = {"in_hand": {"value": 3800, "status": "derived"},
        "repay_total": {"value": 5000, "status": "read"},
        "tenure_days": {"value": 7, "status": "read"},
        "extra": {"value": 1200, "status": "computed"},
        "per_day": {"value": 171, "status": "computed"},
        "apr_simple": {"value": 1647, "status": "computed"}}
UNCLEAR = {**ROW1, "tenure_days": U, "per_day": U, "apr_simple": U}

HI_ROW1 = ("Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye "
           "lautane honge. Yaani 1200 rupaye zyada.")
BN_ROW1 = "আপনি হাতে 3800 টাকা পাবেন। 7 দিনে 5000 টাকা ফেরত দিতে হবে। মানে 1200 টাকা বেশি।"
MR_ROW1 = ("तुम्हाला हातात 3800 रुपये मिळतील. 7 दिवसांत 5000 रुपये परत करावे लागतील. "
           "म्हणजे 1200 रुपये जास्त.")
BN_UNCLEAR = "এই অফারের সব সংখ্যা পরিষ্কার পড়া যায়নি। লোন নেওয়ার আগে ব্যাংক মিত্রকে জিজ্ঞেস করুন।"
MR_UNCLEAR = "या ऑफरचे सगळे आकडे नीट वाचता आले नाहीत. कर्ज घेण्याआधी बँक मित्राला विचारा."


# ---------------------------------------------------------------- config
def test_voice_for_each_language():
    s = config.settings
    assert s.tts_voice("hi") == s.tts_voice_hi == "hi-IN-SwaraNeural"
    assert s.tts_voice("bn") == "bn-IN-TanishaaNeural"
    assert s.tts_voice("mr") == "mr-IN-AarohiNeural"
    assert s.tts_voice("kn") == s.tts_voice_hi and s.tts_voice("") == s.tts_voice_hi


# ---------------------------------------------------------------- the sentence
@pytest.mark.parametrize("lang, expected", [("hi", HI_ROW1), ("bn", BN_ROW1), ("mr", MR_ROW1)])
def test_row1_sentence_in_each_language(lang, expected):
    assert speech_text(ROW1, lang) == expected


@pytest.mark.parametrize("lang, expected", [("bn", BN_UNCLEAR), ("mr", MR_UNCLEAR)])
def test_unclear_sentence_in_each_language(lang, expected):
    assert speech_text(UNCLEAR, lang) == expected


def test_unknown_language_speaks_hindi():
    assert speech_text(ROW1, "kn") == HI_ROW1 and speech_text(ROW1) == HI_ROW1


def test_bn_mr_numbers_are_digits_without_commas():
    big = {**ROW1, "in_hand": {"value": 12500, "status": "read"},
           "repay_total": {"value": 15000, "status": "read"},
           "extra": {"value": 2500, "status": "computed"}}
    for lang in ("bn", "mr"):
        text = speech_text(big, lang)
        assert "12500" in text and "15000" in text and "2500" in text and "," not in text


# ---------------------------------------------------------------- fallback.speak(voice=)
def fake_tts():
    calls = []

    class FakeCommunicate:
        def __init__(self, text, voice):
            calls.append((text, voice))

        async def save(self, path):
            Path(path).write_bytes(b"ID3fake")

    return FakeCommunicate, calls


def test_fallback_speak_uses_the_voice_given(tmp_path, monkeypatch):
    fake, calls = fake_tts()
    monkeypatch.setattr(fallback.edge_tts, "Communicate", fake)
    assert asyncio.run(fallback.speak(BN_ROW1, str(tmp_path / "a.mp3"), voice="bn-IN-TanishaaNeural"))
    assert asyncio.run(fallback.speak(HI_ROW1, str(tmp_path / "b.mp3")))          # no voice -> Hindi
    assert calls == [(BN_ROW1, "bn-IN-TanishaaNeural"), (HI_ROW1, "hi-IN-SwaraNeural")]


# ---------------------------------------------------------------- make_audio(lang)
@pytest.fixture
def audio_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path), voice_enabled=True))
    return tmp_path


def recording_speak(monkeypatch):
    calls = []

    async def speak(text, out_path, **kwargs):
        calls.append((text, kwargs))
        Path(out_path).write_bytes(b"ID3fake")
        return True

    monkeypatch.setattr(fallback, "speak", speak)
    return calls


@pytest.mark.parametrize("lang, voice", [("bn", "bn-IN-TanishaaNeural"), ("mr", "mr-IN-AarohiNeural")])
def test_make_audio_passes_the_language_voice(audio_dir, monkeypatch, lang, voice):
    calls = recording_speak(monkeypatch)
    assert asyncio.run(make_audio("chk_0001", "x", lang)) == "/api/audio/chk_0001.mp3"
    assert calls == [("x", {"voice": voice})]


def test_make_audio_hindi_calls_speak_exactly_as_before(audio_dir, monkeypatch):
    calls = recording_speak(monkeypatch)
    asyncio.run(make_audio("chk_0001", HI_ROW1))
    asyncio.run(make_audio("chk_0002", HI_ROW1, "hi"))
    assert calls == [(HI_ROW1, {}), (HI_ROW1, {})]          # no voice argument for Hindi


# ---------------------------------------------------------------- cache key
def test_cache_key_hindi_unchanged_other_languages_differ():
    photo = b"\xff\xd8 the same photo"
    plain = hashlib.sha256(photo).hexdigest()
    assert cache.image_key(photo) == plain == cache.image_key(photo, "hi")
    keys = {cache.image_key(photo, lang) for lang in ("hi", "bn", "mr")}
    assert len(keys) == 3 and all(len(k) == 64 for k in keys)


# ---------------------------------------------------------------- POST /api/checks with lang
ROW1_READ = {"is_loan_ad": True, "principal": "Rs 5000", "fees": "Rs 1200",
             "repay_total": "Rs 5000", "tenure_days": "7 days"}


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "audio"), cache_dir=str(tmp_path / "cache"),
        voice_enabled=True))
    monkeypatch.setattr(main, "CHECKS", {})
    spoken = []

    async def fake_speak(text, out_path, voice=None):
        spoken.append((text, voice))
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(b"\xff\xf3fake-mp3")
        return True

    monkeypatch.setattr(fallback, "speak", fake_speak)
    reads = []

    def read_image(image_bytes, prompt, engines=("qwen", "gemini"), check=None):
        reads.append(1)
        raw = json.dumps(ROW1_READ)
        if check:
            check(raw)
        return raw, "qwen", 1.2

    monkeypatch.setattr(fallback, "read_image", read_image)
    return spoken, reads


def post_photo(client, lang, data=b"\xff\xd8 fake jpeg"):
    return client.post("/api/checks", files={"image": ("ad.jpg", data, "image/jpeg")},
                       data={"lang": lang, "source": "test"})


@pytest.mark.parametrize("lang, sentence, voice", [
    ("bn", BN_ROW1, "bn-IN-TanishaaNeural"), ("mr", MR_ROW1, "mr-IN-AarohiNeural"),
    ("hi", HI_ROW1, None), ("xx", HI_ROW1, None), (" BN ", BN_ROW1, "bn-IN-TanishaaNeural")])
def test_photo_check_speaks_the_language_asked(client, env, lang, sentence, voice):
    spoken, _ = env
    r = post_photo(client, lang)
    assert r.status_code == 200
    body = r.json()
    assert body["speech_text_hi"] == sentence            # field keeps its contract name
    assert spoken == [(sentence, voice)]
    # numbers on the card are the same whatever the language
    assert {k: v["value"] for k, v in body["numbers"].items()} == {
        "in_hand": 3800, "repay_total": 5000, "tenure_days": 7, "extra": 1200,
        "per_day": 171, "apr_simple": 1647}


def test_text_check_json_lang(client, env, monkeypatch):
    spoken, _ = env

    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "principal": 5000, "fees": 500,
                           "repay_total": 5600, "tenure_days": 7}), "gpt-oss-20b", 0.8

    monkeypatch.setattr(fallback, "read_text", read_text)
    r = client.post("/api/checks", json={"text": "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days.",
                                         "lang": "mr"})
    assert r.status_code == 200
    assert r.json()["speech_text_hi"].startswith("तुम्हाला हातात 4500 रुपये मिळतील.")
    assert spoken[0][1] == "mr-IN-AarohiNeural"


def test_hindi_cache_never_answers_a_bengali_request(client, env):
    spoken, reads = env
    hi = post_photo(client, "hi").json()
    bn = post_photo(client, "bn").json()
    assert len(reads) == 2                                # Bengali was not served from the Hindi cache
    assert bn["cached"] is False and bn["id"] != hi["id"]
    assert bn["speech_text_hi"] == BN_ROW1
    again = post_photo(client, "bn").json()
    assert again["cached"] is True and again["id"] == bn["id"] and len(reads) == 2


def test_cached_bengali_mp3_is_remade_in_bengali(client, env):
    spoken, reads = env
    bn = post_photo(client, "bn").json()
    (Path(config.settings.audio_dir) / f"{bn['id']}.mp3").unlink()      # MP3 lost
    spoken.clear()
    again = post_photo(client, "bn").json()
    assert again["cached"] is True and len(reads) == 1                 # no AI read
    assert spoken == [(BN_ROW1, "bn-IN-TanishaaNeural")]               # remade in Bengali, not Hindi


def test_voice_note_with_lang_bn(client, env, monkeypatch):
    spoken, _ = env
    monkeypatch.setattr(fallback, "transcribe", lambda audio, lang="hi": ("5000 ka loan, 7 din mein 6000 lautana",
                                                               "whisper", 0.9))

    def read_text(prompt, check=None):
        if prompt.startswith("Rewrite"):
            return "5000 ka loan, 7 din mein 6000 lautana", "gpt-oss-20b", 0.5
        return json.dumps({"is_loan_ad": True, "principal": 5000, "repay_total": 6000,
                           "tenure_days": 7}), "gpt-oss-20b", 0.7

    monkeypatch.setattr(fallback, "read_text", read_text)
    r = client.post("/api/checks", files={"audio": ("voice.ogg", b"OggS", "audio/ogg")},
                    data={"lang": "bn", "source": "test"})
    assert r.status_code == 200
    assert r.json()["speech_text_hi"] == "আপনি হাতে 5000 টাকা পাবেন। 7 দিনে 6000 টাকা ফেরত দিতে হবে। মানে 1000 টাকা বেশি।"
