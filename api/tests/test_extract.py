"""extract.py with fake readers: no test calls the internet. Values worked by hand."""
import pytest

from api.core import extract, fallback

# The exact replies Qwen and Gemini gave for the synthetic ad on 13 Nov, 5:40 PM.
QWEN_REAL = ('{   "is_loan_ad": true,   "principal": "Rs 5000",   "in_hand": null,   "fees": "Rs 1200",'
             '   "repay_total": "Rs 5000",   "emi_amount": null,   "emi_count": null,   "tenure_days": "7 days",'
             '   "lender_name": "PaisaTurant",   "app_name": "PaisaTurant" }')
GEMINI_REAL = ('{"is_loan_ad": true, "principal": "5000", "in_hand": null, "fees": "1200", "repay_total": "5000",'
               ' "emi_amount": null, "emi_count": null, "tenure_days": "7", "lender_name": null,'
               ' "app_name": "PaisaTurant"}')
ROW1 = {"principal": 5000.0, "in_hand": None, "fees": 1200.0, "repay_total": 5000.0,
        "emi_amount": None, "emi_count": None, "tenure_days": 7.0}
SMS = "Congrats! Rs 5000 loan approved. Fee Rs 500. Repay Rs 5600 in 7 days."


def numbers(fields):
    return {k: fields[k] for k in extract.NUMBER_KEYS}


def fake_image_reader(monkeypatch, reply):
    """Replace fallback.read_image; runs `check` like the real one does."""
    def read_image(image_bytes, prompt, engines=("qwen", "gemini"), check=None):
        if isinstance(reply, Exception):
            raise reply
        if check:
            check(reply)
        return reply, engines[0], 1.2
    monkeypatch.setattr(fallback, "read_image", read_image)


def fake_text_reader(monkeypatch, reply):
    def read_text(prompt, check=None):
        if isinstance(reply, Exception):
            raise reply
        try:
            if check:
                check(reply)
        except Exception as exc:
            raise fallback.EngineError("bad reply") from exc
        return reply, "gpt-oss-20b", 0.8
    monkeypatch.setattr(fallback, "read_text", read_text)


# ---------------------------------------------------------------- clean-up
def test_strip_fences():
    assert extract.strip_fences('```json\n{"principal": 5000}\n```') == '{"principal": 5000}'
    assert extract.strip_fences('<think>let me see</think>Sure! {"a": 1} hope this helps') == '{"a": 1}'


@pytest.mark.parametrize("raw, expected", [
    ("Rs 5,000", 5000), ("₹1200/-", 1200), ("INR 10,250.50", 10250.5), (7, 7), ("५०००", 5000),
    (None, None), ("null", None), ("", None), (0, None), (-5, None), (True, None)])
def test_to_number(raw, expected):
    assert extract.to_number(raw) == expected


@pytest.mark.parametrize("raw, expected", [
    ("7 days", 7), ("7", 7), (30, 30), ("2 weeks", 14), ("3 months", 90), ("1 saal", 365),
    ("10 din", 10), (None, None), ("0 days", None)])
def test_to_days(raw, expected):
    assert extract.to_days(raw) == expected


def test_parse_real_qwen_and_gemini_replies_give_the_same_numbers():
    assert numbers(extract.parse(QWEN_REAL)) == ROW1
    assert numbers(extract.parse(GEMINI_REAL)) == ROW1
    assert extract.parse(QWEN_REAL)["app_name"] == "PaisaTurant"


def test_parse_percentage_fee_is_worked_out_in_code():
    fields = extract.parse('{"is_loan_ad": true, "principal": "10000", "fees": "10%", "repay_total": 11000}')
    assert fields["fees"] == 1000


def test_parse_percentage_fee_without_principal_is_unknown():
    assert extract.parse('{"is_loan_ad": true, "fees": "10%", "repay_total": 11000}')["fees"] is None


def test_parse_rejects_non_json_and_non_object():
    with pytest.raises(ValueError):
        extract.parse("Sorry, I cannot read this image.")
    with pytest.raises(ValueError):
        extract.parse("[5000, 1200]")


# ---------------------------------------------------------------- photo
def test_image_qwen_reply(monkeypatch):
    fake_image_reader(monkeypatch, "```json\n" + QWEN_REAL + "\n```")
    result = extract.extract_from_image(b"jpeg")
    assert numbers(result["fields"]) == ROW1
    assert result["engines"] == {"read": "qwen", "second_read": None}
    assert set(result["fields"]) == set(extract.FIELD_KEYS)


def test_image_not_a_loan(monkeypatch):
    fake_image_reader(monkeypatch, '{"is_loan_ad": false, "principal": null}')
    with pytest.raises(extract.NotALoan) as err:
        extract.extract_from_image(b"menu photo")
    assert err.value.text_hi == extract.MSG_NOT_A_LOAN


def test_image_no_amounts_read_is_unreadable(monkeypatch):
    fake_image_reader(monkeypatch, '{"is_loan_ad": true, "tenure_days": "7 days"}')
    with pytest.raises(extract.Unreadable) as err:
        extract.extract_from_image(b"blurry photo")
    assert err.value.text_hi == "Photo saaf nahi hai, dobara bhejo."


def test_image_every_reader_failed_is_unreadable(monkeypatch):
    fake_image_reader(monkeypatch, fallback.EngineError("both down"))
    with pytest.raises(extract.Unreadable):
        extract.extract_from_image(b"jpeg")


# ---------------------------------------------------------------- text
def test_text_model_reply(monkeypatch):
    fake_text_reader(monkeypatch, '{"is_loan_ad": true, "principal": "5000", "fees": "500", '
                                  '"repay_total": "5600", "tenure_days": "7 days"}')
    result = extract.extract_from_text(SMS)
    assert numbers(result["fields"]) == {"principal": 5000, "in_hand": None, "fees": 500,
                                         "repay_total": 5600, "emi_amount": None,
                                         "emi_count": None, "tenure_days": 7}
    assert result["engines"]["read"] == "gpt-oss-20b"


def test_text_invented_in_hand_is_dropped(monkeypatch):
    # The SMS never says 4500; the model "helpfully" worked it out. Code ignores it.
    fake_text_reader(monkeypatch, '{"is_loan_ad": true, "principal": 5000, "in_hand": 4500, "fees": 500, '
                                  '"repay_total": 5600, "tenure_days": 7}')
    assert extract.extract_from_text(SMS)["fields"]["in_hand"] is None


def test_text_model_down_uses_regex(monkeypatch):
    fake_text_reader(monkeypatch, fallback.EngineError("429"))
    result = extract.extract_from_text("Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days.")
    assert result["engines"]["read"] == "regex"
    assert numbers(result["fields"]) == {"principal": 5000, "in_hand": None, "fees": 500,
                                         "repay_total": 5600, "emi_amount": None,
                                         "emi_count": None, "tenure_days": 7}


def test_text_model_bad_json_uses_regex(monkeypatch):
    fake_text_reader(monkeypatch, "I think the loan is 5000")
    result = extract.extract_from_text(SMS)
    assert result["engines"]["read"] == "regex"
    assert result["fields"]["principal"] == 5000            # "Rs 5000 loan", not the 500 fee
    assert result["fields"]["repay_total"] == 5600


@pytest.mark.parametrize("sms, expected", [
    ("5000 ka loan lo, 7 din mein 5600 lautana hai. Fees 500.",
     {"principal": 5000, "fees": 500, "repay_total": 5600, "tenure_days": 7}),
    ("Instant loan Rs 10,000! Processing fee 10%. Total repay Rs 11,500 in 2 weeks.",
     {"principal": 10000, "fees": 1000, "repay_total": 11500, "tenure_days": 14}),
    ("Loan amount 20000. EMI Rs 2000 x 12. Tenure 12 months.",
     {"principal": 20000, "emi_amount": 2000, "emi_count": 12, "tenure_days": 360}),
    ("Aapko 4500 haath mein milenge, 7 din baad 5600 wapas karna hai",
     {"in_hand": 4500, "repay_total": 5600, "tenure_days": 7}),
])
def test_regex_backup_on_hinglish_and_english(sms, expected):
    fields = extract.regex_fields(sms)
    for key, value in expected.items():
        assert fields[key] == value, key
    assert fields["is_loan_ad"] is True


def test_text_not_a_loan_from_model(monkeypatch):
    fake_text_reader(monkeypatch, '{"is_loan_ad": false}')
    with pytest.raises(extract.NotALoan):
        extract.extract_from_text("Kal shaam 5 baje milte hain")


def test_text_not_a_loan_from_regex(monkeypatch):
    fake_text_reader(monkeypatch, fallback.EngineError("down"))
    with pytest.raises(extract.NotALoan):
        extract.extract_from_text("Kal shaam milte hain, sabzi le aana")


def test_empty_text_is_unreadable():
    with pytest.raises(extract.Unreadable) as err:
        extract.extract_from_text("   ")
    assert err.value.text_hi == extract.MSG_BAD_TEXT
