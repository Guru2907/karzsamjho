"""Harassment rules H1-H6 (task F1). Hand-written synthetic samples with expected rules.
The text model is faked: no test calls the internet."""
import dataclasses
import json

import pytest

from api.core import config, fallback, harass

POLITE = "Namaste, aapki EMI kal due hai. Kripya samay par bhugtan karein. Dhanyavaad."


def event(at="2026-11-13T11:00:00+05:30", text="", channel="sms", contacted="borrower"):
    return {"at": at, "channel": channel, "contacted": contacted, "text": text}


@pytest.fixture
def ai_down(monkeypatch):
    """The text model is down, so the keyword backup decides H2-H5."""
    def read_text(prompt, check=None):
        raise fallback.EngineError("down")
    monkeypatch.setattr(fallback, "read_text", read_text)


def ai_says(monkeypatch, labels: dict | str):
    """A fake text model answering with these labels (or a raw string)."""
    prompts = []

    def read_text(prompt, check=None):
        prompts.append(prompt)
        raw = labels if isinstance(labels, str) else json.dumps(labels)
        if check:
            try:
                check(raw)
            except Exception as exc:          # like the real read_text: a bad reply is a failure
                raise fallback.EngineError("bad reply") from exc
        return raw, "gpt-oss-20b", 0.6
    monkeypatch.setattr(fallback, "read_text", read_text)
    return prompts


NONE = {"H2": False, "H3": False, "H4": False, "H5": False}


# ---------------------------------------------------------------- the 10 hand-written samples
# (sample, calls_that_day, expected) worked out by hand; the keyword backup decides the text rules
SAMPLES = [
    (event(text=POLITE), 0, []),                                                          # 1 polite 11 AM
    (event("2026-11-13T22:40:00+05:30", "Paisa do warna ghar aa jayenge.", "call"), 1, ["H1", "H2"]),
    (event(text="Aapke bhai ne loan nahi chukaya, family ko sab bata diya hai."), 0, ["H3"]),
    (event(text="Kal tak payment nahi kiya to tumhari photo viral kar denge, sab padosi dekhenge."), 0,
     ["H2", "H4"]),
    (event(text="Police aa rahi hai, tumhare naam ka arrest warrant nikla hai."), 0, ["H5"]),
    (event("2026-11-13T10:15:00+05:30", "", "call"), 6, ["H6"]),                          # 6th call today
    (event("2026-11-14T06:50:00+05:30", "Your family will know you are a defaulter.", "whatsapp",
           "family"), 0, ["H1", "H3", "H4"]),
    (event(text="Saale chor, paisa wapas kar."), 0, ["H2"]),
    (event(text="पैसे दो वरना पुलिस आएगी और जेल जाओगे"), 0, ["H2", "H5"]),                   # Devanagari
    (event(text="Reminder: Rs 5000 due on 15 Nov. Fir se yaad dila rahe hain."), 2, []),  # "fir" = again
]


@pytest.mark.parametrize("sample, calls, expected", SAMPLES, ids=[f"sample{i}" for i in range(1, 11)])
def test_hand_written_samples_with_keyword_backup(ai_down, sample, calls, expected):
    assert harass.label(sample, calls) == expected


def test_polite_11am_reminder_gets_no_rules_from_the_ai_either(monkeypatch):
    ai_says(monkeypatch, NONE)
    assert harass.label(event(text=POLITE), 1) == []


# ---------------------------------------------------------------- H1: time (code only)
@pytest.mark.parametrize("at, breaks", [
    ("2026-11-13T07:59:00+05:30", True), ("2026-11-13T08:00:00+05:30", False),
    ("2026-11-13T19:00:00+05:30", False), ("2026-11-13T19:00:01+05:30", True),
    ("2026-11-13T23:30:00+05:30", True), ("2026-11-13T00:10:00+05:30", True),
    ("2026-11-13T16:30:00+00:00", True),      # 16:30 UTC = 22:00 IST
    ("2026-11-13T05:00:00Z", False),          # 05:00 UTC = 10:30 IST
    ("2026-11-13T21:00:00", True),            # no zone: read as IST
    ("not a time", False), (None, False)])
def test_h1_time_window(at, breaks):
    assert harass.breaks_h1(at) is breaks


def test_h1_hours_come_from_config(monkeypatch):
    late = "2026-11-13T20:30:00+05:30"
    assert harass.breaks_h1(late)
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, h1_latest_hour=21))
    assert not harass.breaks_h1(late)


# ---------------------------------------------------------------- H6: calls in a day (code only)
@pytest.mark.parametrize("calls, breaks", [(4, False), (5, True), (12, True), (0, False)])
def test_h6_our_threshold(calls, breaks):
    assert harass.breaks_h6(calls) is breaks


def test_h6_threshold_from_config_and_labelled_as_ours(monkeypatch):
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, h6_calls_per_day=3))
    assert harass.breaks_h6(3)
    assert "our threshold" in harass.RULES["H6"]


# ---------------------------------------------------------------- H2-H5: the text model
def test_ai_labels_are_used_when_the_model_answers(monkeypatch):
    prompts = ai_says(monkeypatch, {"H2": True, "H3": False, "H4": False, "H5": True})
    text = "Hum aapko dekh lenge, case karenge"
    assert harass.label(event(text=text), 0) == ["H2", "H5"]
    assert prompts[0].endswith(text)


def test_ai_reply_in_fences_is_read(monkeypatch):
    ai_says(monkeypatch, '```json\n{"H2": false, "H3": true, "H4": false, "H5": false}\n```')
    assert harass.label(event(text="Tumhare office mein call karenge"), 0) == ["H3"]


@pytest.mark.parametrize("bad", ["not json", '{"H2": "yes"}', '{"H2": true}', "[]"])
def test_bad_ai_reply_falls_back_to_keywords(monkeypatch, bad):
    ai_says(monkeypatch, bad)
    assert harass.label(event(text="Paisa do warna ghar aa jayenge."), 0) == ["H2"]


def test_code_rules_are_added_to_ai_rules(monkeypatch):
    ai_says(monkeypatch, {**NONE, "H2": True})
    late_family = event("2026-11-13T21:40:00+05:30", "Tum chor ho", "call", "family")
    assert harass.label(late_family, 5) == ["H1", "H2", "H3", "H6"]


def test_empty_text_never_calls_the_model(monkeypatch):
    prompts = ai_says(monkeypatch, {**NONE, "H2": True})
    assert harass.label(event("2026-11-13T22:00:00+05:30", ""), 0) == ["H1"]
    assert prompts == []


@pytest.mark.parametrize("contacted, h3", [("family", True), ("employer", True), ("contacts", True),
                                            ("FAMILY", True), ("borrower", False), (None, False)])
def test_h3_from_who_was_contacted(ai_down, contacted, h3):
    assert ("H3" in harass.label(event(contacted=contacted), 0)) is h3


def test_rules_have_an_english_meaning_and_basis():
    assert set(harass.RULES) == {"H1", "H2", "H3", "H4", "H5", "H6"}
    assert "12 Aug 2022" in harass.RULES_BASIS


def test_keywords_are_a_safety_net_when_the_ai_misses(monkeypatch):
    # Real run 13 Nov: the model said "nothing" for "family ko sab bata diya" (H3).
    ai_says(monkeypatch, NONE)
    sample = event(text="Aapke bhai ne loan nahi chukaya, family ko sab bata diya hai.")
    assert harass.label(sample, 0) == ["H3"]
    assert harass.text_labels(sample["text"]) == ({"H3"}, "gpt-oss-20b+keywords")


def test_ai_alone_when_keywords_add_nothing(monkeypatch):
    ai_says(monkeypatch, {**NONE, "H5": True})
    assert harass.text_labels("Hum legal notice bhejenge") == ({"H5"}, "gpt-oss-20b")
