"""F-1 (demo-pack run, D52): lender.warning and lender.nbfc (D51) must reach whoever calls the API.

They were computed and stored, but CheckResult.lender did not list them, so FastAPI's response_model
dropped them and the bot never showed "RBI ne is company ka NBFC registration radd kiya hai". No internet.
"""
import dataclasses

import pytest

import bot.main as bot
from api.core import config, fallback

WARNING = {"list": "RBI: registration cancelled", "name": "Alok Auto Credit Pvt. Ltd.", "source_type": "official",
           "date": "2026-09-30", "source": "https://rbidocs.rbi.org.in/example.xlsx"}
NBFC = {"name": "Aditya Birla Capital Limited", "list_date": "2026-09-30"}


@pytest.fixture
def api(client, monkeypatch, tmp_path):
    """Real POST /api/checks; the text model is down (the regex backup reads the SMS); no voice."""
    from api import main
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})

    def down(prompt, check=None):
        raise fallback.EngineError("down")
    monkeypatch.setattr(fallback, "read_text", down)
    return client


def lender_says(monkeypatch, **extra):
    from api import main
    monkeypatch.setattr(main.lender, "match_lender", lambda name, text=None: {
        "name_read": "Alok Auto Credit Pvt. Ltd.", "match": "NOT_FOUND", "score": 72.7, "closest": None,
        "list_date": "2026-11-14", "nbfc": None, "warning": None, **extra})


SMS = "Loan Rs 15000. Processing fee Rs 300. Repay Rs 16800 in 180 days."


def test_warning_reaches_the_api_answer_and_the_bot_card(api, monkeypatch):
    lender_says(monkeypatch, warning=WARNING)
    body = api.post("/api/checks", json={"text": SMS}).json()
    assert body["lender"]["warning"] == WARNING                        # was dropped before the fix
    assert body["next_step"]["code"] == "ON_WARNING_LIST"
    card = bot.card_text(body)                                         # the bot's real card code
    assert "⚠️ RBI ne is company ka NBFC registration radd kiya hai: <b>Alok Auto Credit Pvt. Ltd.</b>" in card
    assert "(list: 2026-09-30)" in card
    again = api.get(f"/api/checks/{body['id']}").json()                # the read-back route keeps them too
    assert again["lender"]["warning"] == WARNING


def test_nbfc_reaches_the_api_answer(api, monkeypatch):
    lender_says(monkeypatch, match="FOUND", score=100.0, closest="Kreditbee (EXAMPLE LIMITED)", nbfc=NBFC)
    body = api.post("/api/checks", json={"text": SMS}).json()
    assert body["lender"]["nbfc"] == NBFC and body["lender"]["warning"] is None
    listed = api.get("/api/checks?limit=5").json()
    assert listed[0]["lender"]["nbfc"] == NBFC


def test_no_extras_stay_null(api, monkeypatch):
    lender_says(monkeypatch)
    body = api.post("/api/checks", json={"text": SMS}).json()
    assert body["lender"]["nbfc"] is None and body["lender"]["warning"] is None
    assert "radd kiya" not in bot.card_text(body)
