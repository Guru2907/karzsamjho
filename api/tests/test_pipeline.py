"""POST /api/checks end to end with fake readers and a fake voice: no test calls the internet.

Expected numbers are the hand-worked rows in docs/PLAN.md.
"""
import dataclasses
import json

import pytest

from api import main
from api.core import config, fallback
from api.core.schemas import CheckResult

ROW1 = {"is_loan_ad": True, "principal": "Rs 5000", "fees": "Rs 1200", "repay_total": "Rs 5000",
        "tenure_days": "7 days", "app_name": "PaisaTurant"}
SMS = "Congrats! Rs 5000 loan approved. Fee Rs 500. Repay Rs 5600 in 7 days."
SMS_REPLY = {"is_loan_ad": True, "principal": 5000, "fees": 500, "repay_total": 5600, "tenure_days": 7}
SENTENCE_ROW1 = ("Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye "
                 "lautane honge. Yaani 1200 rupaye zyada.")


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Fresh in-memory store, audio in a temp folder, fake voice that writes a small MP3."""
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path), voice_enabled=True))
    monkeypatch.setattr(main, "CHECKS", {})
    spoken = []

    async def fake_speak(text, out_path):
        spoken.append(text)
        with open(out_path, "wb") as f:
            f.write(b"\xff\xf3fake-mp3")
        return True

    monkeypatch.setattr(fallback, "speak", fake_speak)
    return spoken


def photo_reader(monkeypatch, reply, engine="qwen"):
    def read_image(image_bytes, prompt, engines=("qwen", "gemini"), check=None):
        if isinstance(reply, Exception):
            raise reply
        raw = json.dumps(reply)
        if check:
            check(raw)
        return raw, engine, 1.2
    monkeypatch.setattr(fallback, "read_image", read_image)


def text_reader(monkeypatch, reply):
    def read_text(prompt, check=None):
        if isinstance(reply, Exception):
            raise reply
        return json.dumps(reply), "gpt-oss-20b", 0.8
    monkeypatch.setattr(fallback, "read_text", read_text)


def values(result):
    return {k: (v["value"], v["status"]) for k, v in result["numbers"].items()}


def post_photo(client, data=b"\xff\xd8 fake jpeg"):
    return client.post("/api/checks", files={"image": ("ad.jpg", data, "image/jpeg")},
                       data={"lang": "hi", "source": "test"})


# ---------------------------------------------------------------- photo
def test_photo_row1_full_answer(client, env, monkeypatch):
    photo_reader(monkeypatch, ROW1)
    r = post_photo(client)
    assert r.status_code == 200
    body = r.json()
    CheckResult.model_validate(body)
    assert body["verdict"] == "VERY_COSTLY"
    assert values(body) == {"in_hand": (3800, "derived"), "repay_total": (5000, "read"),
                            "tenure_days": (7, "read"), "extra": (1200, "computed"),
                            "per_day": (171, "computed"), "apr_simple": (1647, "computed")}
    assert body["unverified"] == []
    assert body["speech_text_hi"] == SENTENCE_ROW1 and env == [SENTENCE_ROW1]
    assert body["engines"] == {"read": "qwen", "second_read": None, "speak": "edge-tts"}
    assert body["lender"]["match"] is None and body["lender"]["name_read"] == "PaisaTurant"
    assert body["next_step"]["code"] == "ASK_BANK_MITRA"
    assert body["audio_url"] == f"/api/audio/{body['id']}.mp3"
    audio = client.get(body["audio_url"])
    assert audio.status_code == 200 and audio.headers["content-type"] == "audio/mpeg"
    assert audio.content.startswith(b"\xff\xf3")


def test_photo_emi_without_total_row5(client, env, monkeypatch):
    photo_reader(monkeypatch, {"is_loan_ad": True, "principal": 20000, "emi_amount": 2000,
                               "emi_count": 12, "tenure_days": "12 months"})
    body = post_photo(client).json()
    assert values(body)["repay_total"] == (24000, "derived")
    assert values(body)["extra"] == (4000, "computed")
    assert body["verdict"] == "USUAL"


def test_self_contradicting_ad_cannot_say(client, env, monkeypatch):
    # 5000 - 1200 is 3800, but the ad says you get 4000: never show a verified in-hand.
    photo_reader(monkeypatch, {**ROW1, "in_hand": 4000})
    body = post_photo(client).json()
    assert body["verdict"] == "CANNOT_SAY"
    assert body["numbers"]["in_hand"]["status"] == "unverified"
    assert "in_hand" in body["unverified"]


def test_not_a_loan_photo_gets_hindi_422(client, env, monkeypatch):
    photo_reader(monkeypatch, {"is_loan_ad": False})
    r = post_photo(client)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "NOT_A_LOAN"
    assert r.json()["detail"]["text_hi"].startswith("Yeh loan ka offer nahi lagta")


def test_every_reader_down_gets_photo_saaf_nahi(client, env, monkeypatch):
    photo_reader(monkeypatch, fallback.EngineError("both down"))
    r = post_photo(client)
    assert r.status_code == 422
    assert r.json()["detail"] == {"code": "UNREADABLE", "text_hi": "Photo saaf nahi hai, dobara bhejo."}


def test_empty_upload_is_unreadable(client, env):
    r = post_photo(client, data=b"")
    assert r.status_code == 422 and r.json()["detail"]["code"] == "UNREADABLE"


def test_voice_fails_card_still_comes(client, env, monkeypatch):
    async def broken_speak(text, out_path):
        return False
    monkeypatch.setattr(fallback, "speak", broken_speak)
    photo_reader(monkeypatch, ROW1)
    body = post_photo(client).json()
    assert body["verdict"] == "VERY_COSTLY"
    assert body["audio_url"] is None and body["engines"]["speak"] is None


def test_voice_switched_off(client, env, monkeypatch):
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, voice_enabled=False))
    photo_reader(monkeypatch, ROW1)
    body = post_photo(client).json()
    assert body["audio_url"] is None and env == []          # edge-tts never called


# ---------------------------------------------------------------- text
def test_text_offer_json(client, env, monkeypatch):
    text_reader(monkeypatch, SMS_REPLY)
    r = client.post("/api/checks", json={"text": SMS, "lang": "hi", "source": "test"})
    assert r.status_code == 200
    body = r.json()
    assert values(body) == {"in_hand": (4500, "derived"), "repay_total": (5600, "read"),
                            "tenure_days": (7, "read"), "extra": (1100, "computed"),
                            "per_day": (157, "computed"), "apr_simple": (1275, "computed")}
    assert body["verdict"] == "VERY_COSTLY" and body["engines"]["read"] == "gpt-oss-20b"


def test_text_offer_as_form_field_and_model_down_uses_regex(client, env, monkeypatch):
    text_reader(monkeypatch, fallback.EngineError("429"))
    r = client.post("/api/checks", data={"text": "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days."})
    assert r.status_code == 200
    body = r.json()
    assert body["engines"]["read"] == "regex"
    assert values(body)["extra"] == (1100, "computed")


def test_text_not_a_loan(client, env, monkeypatch):
    text_reader(monkeypatch, {"is_loan_ad": False})
    r = client.post("/api/checks", json={"text": "Kal mandi mein milte hain"})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "NOT_A_LOAN"


def test_bad_requests(client, env):
    assert client.post("/api/checks", json={}).status_code == 422
    assert client.post("/api/checks", content=b"hi", headers={"content-type": "text/plain"}).status_code == 415


# ---------------------------------------------------------------- get, list, audio, stats
def test_get_list_and_stats(client, env, monkeypatch):
    photo_reader(monkeypatch, ROW1)
    first = post_photo(client).json()
    text_reader(monkeypatch, SMS_REPLY)
    second = client.post("/api/checks", json={"text": SMS}).json()
    assert client.get(f"/api/checks/{first['id']}").json() == first
    assert [c["id"] for c in client.get("/api/checks?limit=20").json()] == [second["id"], first["id"]]
    assert len(client.get("/api/checks?limit=1").json()) == 1
    assert client.get("/api/checks/chk_9999").status_code == 404
    stats = client.get("/api/stats").json()
    assert stats["checks"] == 2 and stats["extra_rupees_flagged"] == 1200 + 1100


def test_audio_only_for_known_safe_ids(client, env):
    assert client.get("/api/audio/chk_9999.mp3").status_code == 404
    assert client.get("/api/audio/..%2F..%2F.env.mp3").status_code == 404


# ---------------------------------------------------------------- second reading (B6)
def two_readers(monkeypatch, qwen, gemini):
    """Qwen and Gemini give different replies; follows the engine order like fallback does."""
    calls = []

    def read_image(image_bytes, prompt, engines=("qwen", "gemini"), check=None):
        for name in engines:
            reply = {"qwen": qwen, "gemini": gemini}[name]
            calls.append(name)
            if isinstance(reply, Exception):
                continue
            raw = json.dumps(reply)
            if check:
                check(raw)
            return raw, name, 1.0
        raise fallback.EngineError("all down")
    monkeypatch.setattr(fallback, "read_image", read_image)
    return calls


def test_numbers_add_up_no_second_reading(client, env, monkeypatch):
    calls = two_readers(monkeypatch, ROW1, ROW1)
    body = post_photo(client).json()
    assert calls == ["qwen"] and body["engines"]["second_read"] is None


def test_invented_in_hand_is_caught_by_the_second_reader(client, env, monkeypatch):
    calls = two_readers(monkeypatch, {**ROW1, "in_hand": 4000}, ROW1)
    body = post_photo(client).json()
    assert calls == ["qwen", "gemini"]
    assert body["engines"] == {"read": "qwen", "second_read": "gemini", "speak": "edge-tts"}
    assert values(body)["in_hand"] == (3800, "derived")        # worked out from 5000 - 1200
    assert body["verdict"] == "VERY_COSTLY" and body["unverified"] == []
    assert body["speech_text_hi"] == SENTENCE_ROW1


def test_both_readers_see_a_contradicting_ad(client, env, monkeypatch):
    two_readers(monkeypatch, {**ROW1, "in_hand": 4000}, {**ROW1, "in_hand": 4000})
    body = post_photo(client).json()
    assert body["engines"]["second_read"] == "gemini"
    assert body["verdict"] == "CANNOT_SAY"
    assert body["numbers"]["in_hand"]["status"] == "unverified"
    assert {"in_hand", "principal", "fees"} <= set(body["unverified"])


def test_second_reader_down_means_cannot_say(client, env, monkeypatch):
    two_readers(monkeypatch, {**ROW1, "in_hand": 4000}, fallback.EngineError("gemini down"))
    body = post_photo(client).json()
    assert body["engines"]["second_read"] is None
    assert body["verdict"] == "CANNOT_SAY"
    assert body["numbers"]["in_hand"]["status"] == "unverified"


def test_readers_disagree_on_repay(client, env, monkeypatch):
    emi = {"is_loan_ad": True, "principal": 20000, "emi_amount": 2000, "emi_count": 12,
           "tenure_days": 360}
    two_readers(monkeypatch, {**emi, "repay_total": 25000}, {**emi, "repay_total": 24000})
    body = post_photo(client).json()
    # 2000 x 12 = 24000 is derived again once the disputed printed total is set aside
    assert values(body)["repay_total"] == (24000, "derived")
    assert "repay_total" not in body["unverified"]
    assert body["verdict"] == "USUAL"


def test_qwen_429_then_mismatch_asks_qwen_second(client, env, monkeypatch):
    calls = []

    def read_image(image_bytes, prompt, engines=("qwen", "gemini"), check=None):
        calls.append(engines)
        if engines == ("qwen", "gemini"):        # first read: Qwen 429 -> Gemini answers
            return json.dumps({**ROW1, "in_hand": 4000}), "gemini", 4.0
        return json.dumps(ROW1), engines[0], 1.0
    monkeypatch.setattr(fallback, "read_image", read_image)
    body = post_photo(client).json()
    assert calls == [("qwen", "gemini"), ("qwen",)]
    assert body["engines"]["read"] == "gemini" and body["engines"]["second_read"] == "qwen"


def test_text_never_gets_a_second_reading(client, env, monkeypatch):
    text_reader(monkeypatch, {"is_loan_ad": True, "principal": 5000, "fees": 500, "in_hand": 4000,
                              "repay_total": 5600, "tenure_days": 7})
    called = []
    monkeypatch.setattr(fallback, "read_image", lambda *a, **k: called.append(1))
    body = client.post("/api/checks", json={"text": "Loan Rs 5000. Fee Rs 500. You get Rs 4000. "
                                                    "Repay Rs 5600 in 7 days."}).json()
    assert called == [] and body["verdict"] == "CANNOT_SAY"
