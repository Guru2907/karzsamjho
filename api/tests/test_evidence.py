"""Evidence PDF, masking and hashes (task F3). Synthetic data only; no internet."""
from datetime import datetime

import pytest

from api.core import evidence


def chained(events):
    """Give synthetic events real hashes, like the F2 endpoint will."""
    prev = evidence.GENESIS
    out = []
    for ev in events:
        ev = {**ev, "prev_hash": prev}
        ev["hash"] = evidence.event_hash(prev, ev)
        prev = ev["hash"]
        out.append(ev)
    return out


CASE = {
    "id": "case_0007", "borrower_name": "Raju (sample)", "lender_name": "QuickCash",
    "check_id": "chk_0042", "route": None, "opened_at": "2026-11-13T12:00:00+05:30", "day": 1,
    "events": chained([
        {"id": "evt_0001", "at": "2026-11-13T21:40:00+05:30", "channel": "call", "contacted": "borrower",
         "text": "Paisa do warna ghar aa jayenge. Aadhaar 1234 5678 9012 hamare paas hai.",
         "rules": ["H1", "H2"]},
        {"id": "evt_0002", "at": "2026-11-14T10:15:00+05:30", "channel": "whatsapp", "contacted": "family",
         "text": "Aapke bhai ne loan nahi chukaya. Rs 5,000 abhi bhejo.", "rules": ["H3"]},
        {"id": "evt_0003", "at": "2026-11-14T10:20:00+05:30", "channel": "sms", "contacted": "borrower",
         "text": "पैसे दो वरना पुलिस आएगी", "rules": ["H2", "H5"]},
    ]),
}


def pdf_text(case=CASE) -> str:
    """The PDF with compression off, as text, so the words can be checked."""
    raw = evidence.build_pdf(case, compress=False).decode("latin-1")
    return raw.replace("\\(", "(").replace("\\)", ")")      # PDF text escapes its brackets


# ---------------------------------------------------------------- masking
@pytest.mark.parametrize("text, expected", [
    ("Aadhaar 1234 5678 9012", "Aadhaar XXXX XXXX 9012"),
    ("id:123456789012.", "id:XXXX XXXX 9012."),
    ("1234-5678-9012 and 1111 2222 3333", "XXXX XXXX 9012 and XXXX XXXX 3333"),
    ("phone 9876543210", "phone 9876543210"),             # 10 digits: not an Aadhaar number
    ("1234567890123", "1234567890123"),                   # 13 digits: left alone
    ("Rs 5,000 in 7 days", "Rs 5,000 in 7 days"),
    ("", ""), (None, ""),
])
def test_mask(text, expected):
    assert evidence.mask(text) == expected


# ---------------------------------------------------------------- the PDF
def test_pdf_starts_with_pdf_and_ends_properly():
    pdf = evidence.build_pdf(CASE)
    assert pdf.startswith(b"%PDF") and pdf.rstrip().endswith(b"%%EOF")


def test_pdf_never_contains_the_full_12_digit_number():
    text = pdf_text()
    assert "1234 5678 9012" not in text and "123456789012" not in text
    assert "XXXX XXXX 9012" in text


def test_pdf_has_every_section_in_english():
    text = pdf_text()
    for words in ("KarzSamjho: harassment evidence", "Case case_0007", "QuickCash", "Day 1 of 30",
                  "Rules broken", "RBI circular on recovery agents, 12 Aug 2022", "Timeline (3 contacts)",
                  "Record integrity (hash chain)", "Where to complain", "Complaint draft",
                  "Contact before 08:00 or after 19:00", "Threats or abusive language",
                  "13 Nov 2026, 9:40 PM", "Paisa do warna ghar aa jayenge."):
        assert words in text, words


def test_pdf_shows_every_hash():
    text = pdf_text()
    for ev in CASE["events"]:
        assert ev["hash"] in text and ev["prev_hash"] in text


def test_devanagari_message_is_noted_not_garbled():
    text = pdf_text()
    assert "Written in Hindi / Bengali / Marathi script" in text


def test_rupee_sign_becomes_rs():
    assert evidence.pdf_text("₹5,000 abhi bhejo") == "Rs 5,000 abhi bhejo"


def test_threats_add_the_police_route_when_no_route_is_set():
    text = pdf_text()
    assert "cms.rbi.org.in" in text and "1930" in text and "112" in text


def test_route_from_the_case_is_used():
    text = pdf_text({**CASE, "route": "Sachet portal + cybercrime.gov.in / 1930"})
    assert "Sachet portal + cybercrime.gov.in / 1930" in text
    assert "cms.rbi.org.in" not in text                      # only the case's route + police


def test_complaint_draft_counts_and_names():
    lines = evidence.complaint_draft(CASE, evidence.rule_counts(CASE["events"]))
    letter = " ".join(lines)
    assert "Raju (sample)" in letter and "QuickCash" in letter and "3 times" in letter
    assert "H2 threats or abusive language (2 times)" in letter and "H3" in letter


def test_empty_case_still_makes_a_pdf():
    text = pdf_text({"id": "case_0001", "borrower_name": "Raju", "lender_name": "X",
                     "opened_at": "2026-11-13T12:00:00+05:30", "events": []})
    assert "No contacts logged yet." in text and "No rule was broken" in text


def test_time_format_has_no_leading_zeros():
    assert evidence._when("2026-11-03T09:05:00+05:30") == "3 Nov 2026, 9:05 AM IST"
    assert evidence._when("2026-11-13T16:10:00+00:00") == "13 Nov 2026, 9:40 PM IST"   # UTC -> IST


def test_day_counter():
    assert evidence.case_day({"day": 4}) == 4
    opened = {"opened_at": "2026-11-13T12:00:00+05:30"}
    assert evidence.case_day(opened, datetime.fromisoformat("2026-11-13T23:00:00+05:30")) == 1
    assert evidence.case_day(opened, datetime.fromisoformat("2026-11-15T09:00:00+05:30")) == 3
    assert evidence.case_day({"opened_at": "nonsense"}) is None


# ---------------------------------------------------------------- hash chain helpers
def test_chain_verifies_and_any_edit_breaks_it():
    events = [dict(ev) for ev in CASE["events"]]
    assert evidence.verify_chain(events)
    events[1]["text"] = "Kuch nahi kaha."                     # someone edits one entry
    assert not evidence.verify_chain(events)


def test_removing_an_entry_breaks_the_chain():
    events = [dict(ev) for ev in CASE["events"]]
    assert not evidence.verify_chain([events[0], events[2]])


def test_hash_is_sha256_of_prev_plus_fields():
    ev = CASE["events"][0]
    assert len(ev["hash"]) == 64 and ev["prev_hash"] == "0" * 64
    assert evidence.event_hash("0" * 64, ev) == ev["hash"]
    assert evidence.event_hash("1" * 64, ev) != ev["hash"]


def test_hash_matches_the_f2_definition_in_main_py():
    # main.py event_hash (F2, PR #29): SHA-256(prev_hash + compact sorted JSON of at/channel/contacted/text/rules)
    import hashlib
    import json
    ev = CASE["events"][0]
    fields = {k: ev.get(k) for k in ("at", "channel", "contacted", "text", "rules")}
    body = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert evidence.event_hash("0" * 64, ev) == hashlib.sha256(("0" * 64 + body).encode("utf-8")).hexdigest()
    assert evidence.event_hash("0" * 64, {**ev, "id": "evt_9999"}) == ev["hash"]   # the id is not hashed
