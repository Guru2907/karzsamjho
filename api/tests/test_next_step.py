"""C2: exactly ONE next step per check (verdict x lender match x pay_first). No internet."""
import dataclasses

import pytest

from api.core import fallback, next_step

VERDICTS = ["USUAL", "COSTLY", "VERY_COSTLY", "CANNOT_SAY"]
MATCHES = ["FOUND", "SIMILAR", "NOT_FOUND", None]          # None = not checked (RBI list empty)
PAY_FIRST = [None, 0, 1499.0]                              # 0 counts as "not asked"
FORBIDDEN = ["safe", "illegal", "fake", "surakshit", "farzi", "nakli", "gair-kanooni"]


def expected(verdict, match, pay_first):
    """The order from docs/PLAN.md "Handover at 1:20 AM", C2, worked out by hand."""
    if pay_first:
        return "DO_NOT_PAY_FIRST"
    if match == "NOT_FOUND":
        return "NOT_IN_RBI_LIST"
    if match == "SIMILAR":
        return "CHECK_APP_NAME"
    return {"USUAL": "KEEP_PAPERS", "COSTLY": "ASK_BANK_MITRA",
            "VERY_COSTLY": "FIND_CHEAPER", "CANNOT_SAY": "SEND_CLEARER"}[verdict]


@pytest.mark.parametrize("pay_first", PAY_FIRST)
@pytest.mark.parametrize("match", MATCHES)
@pytest.mark.parametrize("verdict", VERDICTS)
def test_every_combination_gives_exactly_one_step(verdict, match, pay_first):
    step = next_step.next_step(verdict, match, pay_first)
    assert set(step) == {"code", "text_hi"}                 # one step: one code, one sentence
    assert step["code"] == expected(verdict, match, pay_first)
    assert step["text_hi"] == next_step.STEPS[step["code"]]


def test_not_checked_lender_falls_through_to_the_verdict():
    assert next_step.next_step("USUAL", None)["code"] == "KEEP_PAPERS"
    assert next_step.next_step("VERY_COSTLY", None)["code"] == "FIND_CHEAPER"


def test_found_lender_still_follows_the_verdict():
    # being in RBI's list does not make a costly loan cheap
    assert next_step.next_step("VERY_COSTLY", "FOUND")["code"] == "FIND_CHEAPER"


def test_unknown_verdict_never_claims_more_than_we_know():
    assert next_step.next_step("SOMETHING_NEW", None)["code"] == "SEND_CLEARER"


def test_exact_sentences():
    assert next_step.STEPS["DO_NOT_PAY_FIRST"] == ("Paise mat bhejo. Loan se pehle paise maangna dhokha "
                                                   "ho sakta hai. Shikayat: 1930 ya cybercrime.gov.in")
    assert next_step.STEPS["FIND_CHEAPER"] == ("Yeh loan bahut mehenga hai. Bank, SHG ya cooperative "
                                               "se sasta loan poochho.")
    assert "sachet.rbi.org.in" in next_step.STEPS["NOT_IN_RBI_LIST"]


@pytest.mark.parametrize("code", list(next_step.STEPS))
def test_never_safe_illegal_or_fake(code):
    words = next_step.STEPS[code].lower()
    assert not any(w in words for w in FORBIDDEN)


# ---------------------------------------------------------------- through the API
@pytest.fixture
def api(client, monkeypatch, tmp_path):
    """Real POST /api/checks with the text model down (regex backup reads the SMS), no voice."""
    from api import main
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})

    def read_text(prompt, check=None):
        raise fallback.EngineError("down")
    monkeypatch.setattr(fallback, "read_text", read_text)
    return client


@pytest.mark.parametrize("sms, verdict, code", [
    ("Loan Rs 10000. Repay Rs 10250 in 30 days.", "USUAL", "KEEP_PAPERS"),          # 30% a year
    ("Loan Rs 10000. Repay Rs 10500 in 30 days.", "COSTLY", "ASK_BANK_MITRA"),      # 61% a year
    ("Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days.", "VERY_COSTLY", "FIND_CHEAPER"),
])
def test_api_card_carries_the_step_for_its_verdict(api, sms, verdict, code):
    body = api.post("/api/checks", json={"text": sms}).json()
    assert body["verdict"] == verdict
    assert body["next_step"] == {"code": code, "text_hi": next_step.STEPS[code]}


def test_api_lender_not_in_rbi_list_wins_over_the_verdict(api, monkeypatch):
    from api import main
    monkeypatch.setattr(main.lender, "match_lender", lambda name, text=None: {
        "name_read": "QuickCash", "match": "NOT_FOUND", "score": 41.0, "closest": None,
        "list_date": "2026-11-12"})
    body = api.post("/api/checks", json={"text": "Loan Rs 10000. Repay Rs 10250 in 30 days."}).json()
    assert body["verdict"] == "USUAL"
    assert body["next_step"]["code"] == "NOT_IN_RBI_LIST"
