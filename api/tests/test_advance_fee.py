"""B9 (money asked before the loan) and B10 (lakh / crore / hazaar). No internet.

The three scam texts are Anam's, from api/data/offers/sms_offers.json (PR #19).
"""
import json

import pytest

from api.core import extract, fallback

SCAM1 = ("Congratulations! Your personal loan of ₹5,00,000 is pre-approved. "
         "Apply now and get instant disbursal.")
SCAM2 = "Urgent! Your loan is approved. Pay ₹1,499 processing fee to release funds. Contact us immediately."
SCAM3 = "Guaranteed ₹5 lakh loan without documents. Pay refundable insurance charges of ₹1,200 now."


# ---------------------------------------------------------------- B10 lakh / crore
@pytest.mark.parametrize("raw, expected", [
    ("₹5 lakh", 500000), ("5 Lakh", 500000), ("1.5 lakh", 150000), ("2 lakhs", 200000),
    ("3 lac", 300000), ("2 crore", 20000000), ("1.2 cr", 12000000), ("50 hazaar", 50000),
    ("5k", 5000), ("10 thousand", 10000), ("५ लाख", 500000), ("5,00,000", 500000),
    ("Rs 5000", 5000), (7, 7)])
def test_lakh_crore_hazaar(raw, expected):
    assert extract.to_number(raw) == expected


def test_days_never_get_a_lakh_unit():
    assert extract.to_days("2 weeks") == 14 and extract.to_days("7 din") == 7


def test_regex_backup_reads_lakh():
    fields = extract.regex_fields("Loan amount 2 lakh. Repay 2.4 lakh in 12 months.")
    assert fields["principal"] == 200000 and fields["repay_total"] == 240000
    assert fields["tenure_days"] == 360


def test_lakh_written_in_words_is_not_dropped_as_invented(monkeypatch):
    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "principal": "5 lakh"}), "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "read_text", read_text)
    assert extract.extract_from_text(SCAM3)["fields"]["principal"] == 500000


# ---------------------------------------------------------------- B9 pay before the loan
@pytest.mark.parametrize("text, amount", [
    (SCAM1, None), (SCAM2, 1499), (SCAM3, 1200),
    ("Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days.", None),            # normal offer
    ("Pay Rs 5600 in 7 days.", None),                                          # repaying, no charge word
    ("Processing fee Rs 500 will be deducted from your loan.", None),          # deducted, not paid
    ("Pay now Rs 5600 within 7 days.", None),                                  # repaying, no charge word
    ("Loan pane ke liye 999 rupaye registration fee abhi bhejo.", 999),        # Hinglish
])
def test_pay_first_rule(text, amount):
    assert extract.pay_first_in_text(text) == amount


def test_ai_pay_first_clears_the_same_amount_from_fees():
    fields = extract.parse('{"is_loan_ad": true, "fees": "Rs 1,499", "pay_first": "Rs 1,499"}')
    assert fields["pay_first"] == 1499 and fields["fees"] is None


def model_down(monkeypatch):
    def read_text(prompt, check=None):
        raise fallback.EngineError("down")
    monkeypatch.setattr(fallback, "read_text", read_text)


def test_scam2_with_no_loan_numbers_still_answers(monkeypatch):
    model_down(monkeypatch)
    result = extract.extract_from_text(SCAM2)          # no principal: used to be "samajh nahi aaya"
    assert result["fields"]["pay_first"] == 1499
    assert result["fields"]["fees"] is None             # paid first, not deducted


def test_scam3_regex_path(monkeypatch):
    model_down(monkeypatch)
    fields = extract.extract_from_text(SCAM3)["fields"]
    assert fields["pay_first"] == 1200 and fields["principal"] == 500000 and fields["fees"] is None


def test_ai_misses_it_code_rule_catches_it(monkeypatch):
    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "fees": 1499}), "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "read_text", read_text)
    fields = extract.extract_from_text(SCAM2)["fields"]
    assert fields["pay_first"] == 1499 and fields["fees"] is None


def test_ai_invented_pay_first_is_dropped(monkeypatch):
    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "principal": 5000, "repay_total": 5600,
                           "tenure_days": 7, "pay_first": 999}), "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "read_text", read_text)
    fields = extract.extract_from_text("Loan Rs 5000. Repay Rs 5600 in 7 days.")["fields"]
    assert fields["pay_first"] is None                  # 999 is not in the message


# ---------------------------------------------------------------- end to end
def test_api_scam2_warns_in_card_and_voice(client, monkeypatch, tmp_path):
    import dataclasses
    from api import main
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})
    model_down(monkeypatch)
    r = client.post("/api/checks", json={"text": SCAM2})
    assert r.status_code == 200
    body = r.json()
    assert body["next_step"]["code"] == "DO_NOT_PAY_FIRST"
    assert "1930" in body["next_step"]["text_hi"]
    assert body["speech_text_hi"].startswith("Savdhaan! Yeh offer loan dene se pehle aapse 1499 rupaye")
    assert body["verdict"] == "CANNOT_SAY"


def test_api_normal_offer_has_no_warning(client, monkeypatch, tmp_path):
    import dataclasses
    from api import main
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})
    model_down(monkeypatch)
    body = client.post("/api/checks", json={"text": "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days."}).json()
    assert body["next_step"]["code"] == "ASK_BANK_MITRA"
    assert not body["speech_text_hi"].startswith("Savdhaan")


@pytest.mark.parametrize("lang, starts", [
    ("hi", "Savdhaan! Yeh offer loan dene se pehle aapse 1499 rupaye"),
    ("bn", "সাবধান! এই অফার লোন দেওয়ার আগেই আপনার কাছ থেকে 1499 টাকা"),
    ("mr", "सावधान! ही ऑफर कर्ज देण्याआधीच तुमच्याकडून 1499 रुपये"),
])
def test_warning_is_in_the_voice_language(client, monkeypatch, tmp_path, lang, starts):
    import dataclasses
    from api import main
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})
    model_down(monkeypatch)
    body = client.post("/api/checks", json={"text": SCAM2, "lang": lang}).json()
    assert body["speech_text_hi"].startswith(starts)
    if lang != "hi":
        assert "Savdhaan" not in body["speech_text_hi"]          # no Hinglish read by a bn/mr voice
