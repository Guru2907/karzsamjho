"""F2: real cases + events with a hash chain (A3 database). No internet; harass.label is faked."""
import hashlib
import json
import re
from datetime import datetime, timedelta

import pytest

from api import main
from api.core import config, db, harass

GENESIS = "0" * 64


@pytest.fixture
def fake_label(monkeypatch):
    """Stands in for Siddeshwar's F1 harass.label; records what it was given."""
    seen = []

    def label(event, calls_that_day):
        seen.append((event["text"], calls_that_day))
        rules = set()
        if event["at"][11:13] >= "19" or event["at"][11:13] < "08":
            rules.add("H1")
        if "warna" in event["text"].lower():
            rules.add("H2")
        if calls_that_day >= 5:
            rules.add("H6")
        return sorted(rules)
    monkeypatch.setattr(harass, "label", label, raising=False)
    return seen


def new_case(client):
    return client.post("/api/cases", json={"borrower_name": "Raju (test)", "lender_name": "QuickCash",
                                           "check_id": "chk_0001"}).json()


def log_event(client, case_id, at, text="Paisa do", channel="call", contacted="borrower"):
    return client.post(f"/api/cases/{case_id}/events",
                       json={"at": at, "channel": channel, "contacted": contacted, "text": text})


def test_new_case_is_real_not_sample(client):
    case = new_case(client)
    assert re.fullmatch(r"case_[0-9a-f]{16}", case["id"]) and case["events"] == [] and case["day"] == 1
    assert re.fullmatch(r"[1-9]\d{7}", case["code"]) and case["source"] == "app"
    assert case["lender_name"] == "QuickCash" and case["check_id"] == "chk_0001"
    assert client.get("/api/cases/case_0007").status_code == 404          # the old sample is gone


def test_hash_chain(client, fake_label):
    case = new_case(client)
    first = log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna ghar aa jayenge").json()
    second = log_event(client, case["id"], "2026-11-14T10:15:00+05:30", "Kal tak bhejo",
                       channel="whatsapp", contacted="family").json()
    assert first["prev_hash"] == GENESIS
    fields = {"at": "2026-11-13T21:40:00+05:30", "channel": "call", "contacted": "borrower",
              "text": "Paisa do warna ghar aa jayenge", "rules": ["H1", "H2"]}
    expected = hashlib.sha256((GENESIS + json.dumps(fields, sort_keys=True, ensure_ascii=False,
                                                    separators=(",", ":"))).encode()).hexdigest()
    assert first["hash"] == expected                                       # worked out by hand here
    assert second["prev_hash"] == first["hash"]                            # the chain links
    assert first["rules"] == ["H1", "H2"] and second["rules"] == []
    stored = client.get(f"/api/cases/{case['id']}").json()
    assert [e["id"] for e in stored["events"]] == [first["id"], second["id"]]


def test_h6_gets_calls_that_day_including_this_one(client, fake_label):
    case = new_case(client)
    for hour in (9, 10, 11, 12):
        log_event(client, case["id"], f"2026-11-13T{hour:02d}:00:00+05:30")
    log_event(client, case["id"], "2026-11-13T13:00:00+05:30", channel="sms")       # not a call
    fifth = log_event(client, case["id"], "2026-11-13T14:00:00+05:30").json()
    next_day = log_event(client, case["id"], "2026-11-14T09:00:00+05:30").json()
    assert [n for _, n in fake_label] == [1, 2, 3, 4, 4, 5, 1]
    assert "H6" in fifth["rules"] and "H6" not in next_day["rules"]


def test_rules_missing_or_failing_still_stores_the_event(client, monkeypatch):
    case = new_case(client)
    monkeypatch.delattr(harass, "label", raising=False)                     # F1 not merged yet
    r = log_event(client, case["id"], "2026-11-13T21:40:00+05:30")
    assert r.status_code == 200 and r.json()["rules"] == []

    def broken(event, calls):
        raise RuntimeError("AI down")
    monkeypatch.setattr(harass, "label", broken, raising=False)
    r = log_event(client, case["id"], "2026-11-13T21:50:00+05:30")
    assert r.status_code == 200 and r.json()["rules"] == []
    assert len(client.get(f"/api/cases/{case['id']}").json()["events"]) == 2


def test_time_without_zone_is_ist_and_bad_time_is_refused(client, fake_label):
    case = new_case(client)
    ok = log_event(client, case["id"], "2026-11-13T21:40:00").json()
    assert ok["at"] == "2026-11-13T21:40:00+05:30" and "H1" in ok["rules"]
    bad = log_event(client, case["id"], "yesterday night")
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "BAD_TIME"


def test_missing_case(client):
    assert client.get("/api/cases/case_9999").status_code == 404
    assert log_event(client, "case_9999", "2026-11-13T21:40:00+05:30").status_code == 404


def test_day_counter(client):
    case = new_case(client)
    when = (datetime.now(db.IST) - timedelta(days=3)).isoformat(timespec="seconds")
    _sql("UPDATE cases SET opened_at = ? WHERE id = ?", when, case["id"])    # pretend it opened 3 days ago
    assert client.get(f"/api/cases/{case['id']}").json()["day"] == 4


def test_chain_survives_a_restart(client, fake_label, monkeypatch):
    case = new_case(client)
    first = log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna").json()
    db._ready.clear()                                                       # a fresh process
    second = log_event(client, case["id"], "2026-11-13T22:00:00+05:30").json()
    assert second["prev_hash"] == first["hash"]
    events = client.get(f"/api/cases/{case['id']}").json()["events"]
    assert all(main.event_hash(e["prev_hash"], e) == e["hash"] for e in events)


def test_there_is_no_list_of_every_case(client):
    """D59: nobody can see every case. A case is found by its code (or its secret id)."""
    new_case(client)
    assert client.get("/api/cases").status_code == 405       # the route is gone (only POST is left)


def test_case_is_found_by_its_code_with_or_without_the_space(client):
    case = new_case(client)
    code = case["code"]
    for typed in (code, f"{code[:4]} {code[4:]}"):
        found = client.get(f"/api/cases/code/{typed}")
        assert found.status_code == 200 and found.json()["id"] == case["id"]


def test_wrong_code_is_404_in_hindi(client):
    new_case(client)
    for wrong in ("12345678", "1234", "abcdefgh"):
        r = client.get(f"/api/cases/code/{wrong}")
        assert r.status_code == 404 and "nahi mila" in r.json()["detail"]["text_hi"]


def test_codes_are_unique_and_never_change(client):
    cases = [new_case(client) for _ in range(20)]
    assert len({c["code"] for c in cases}) == 20 and len({c["id"] for c in cases}) == 20
    one = cases[0]
    log_event(client, one["id"], "2026-11-13T21:40:00+05:30")
    assert client.get(f"/api/cases/{one['id']}").json()["code"] == one["code"]


def test_phone_is_stored_masked_only(client):
    case = client.post("/api/cases", json={"borrower_name": "Raju", "lender_name": "QuickCash",
                                           "borrower_phone": "+91 98765 43210"}).json()
    assert case["borrower_phone"] == "XXXXXX 3210"
    later = client.put(f"/api/cases/{new_case(client)['id']}/phone", json={"borrower_phone": "9123456789"})
    assert later.status_code == 200 and later.json()["borrower_phone"] == "XXXXXX 6789"
    assert client.put("/api/cases/case_nope/phone", json={"borrower_phone": "9123456789"}).status_code == 404
    assert client.put(f"/api/cases/{case['id']}/phone", json={"borrower_phone": "12"}).status_code == 422


def test_bot_memory_for_a_chat(client):
    """D59: the bot's /bhasha language and the chat's case live in the database, by a scrambled key."""
    key = "ab" * 20
    assert client.get(f"/api/telegram/{key}").json() == {"lang": None, "case_id": None, "code": None,
                                                         "has_phone": False, "closed": False}
    case = client.post("/api/cases", json={"borrower_name": "Raju", "lender_name": "QuickCash",
                                           "telegram_chat": key}).json()
    assert case["source"] == "telegram" and "telegram_chat" not in case          # the key is never shown
    assert client.put(f"/api/telegram/{key}", json={"lang": "bn"}).status_code == 200
    state = client.get(f"/api/telegram/{key}").json()
    assert state == {"lang": "bn", "case_id": case["id"], "code": case["code"], "has_phone": False, "closed": False}
    assert client.get("/api/telegram/not-a-key").status_code == 404
    assert client.put(f"/api/telegram/{key}", json={"lang": "xx"}).status_code == 422


# ---------------------------------------------------------------- the evidence PDF route (F3 wired)
def test_evidence_pdf_route(client, fake_label):
    case = new_case(client)
    log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna, Aadhaar 1234 5678 9012")
    r = client.get(f"/api/cases/{case['id']}/evidence.pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF") and len(r.content) > 1000
    assert client.get("/api/cases/case_9999/evidence.pdf").status_code == 404


def test_evidence_pdf_masks_and_has_every_event(client, fake_label, monkeypatch):
    from api.core import evidence
    seen = {}
    real = evidence.build_pdf
    monkeypatch.setattr(evidence, "build_pdf", lambda case, **kw: (seen.update(case=case), real(case, compress=False))[1])
    case = new_case(client)
    log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna, Aadhaar 1234 5678 9012")
    log_event(client, case["id"], "2026-11-14T10:00:00+05:30", "Kal tak bhejo")
    body = client.get(f"/api/cases/{case['id']}/evidence.pdf").content
    assert len(seen["case"]["events"]) == 2 and seen["case"]["day"] == 1
    assert b"1234 5678 9012" not in body                              # the 12-digit number is masked


# ---------------------------------------------------------------- F4 verify
def _three_events(client):
    case = new_case(client)
    for at, text in (("2026-11-13T21:40:00+05:30", "Paisa do warna"), ("2026-11-14T10:00:00+05:30", "Kal tak"),
                     ("2026-11-14T22:30:00+05:30", "Ghar aa jayenge")):
        log_event(client, case["id"], at, text)
    return case["id"]


def _sql(query, *args):
    """A hand edit straight in the database, behind the API's back (SQLite or Postgres, D58)."""
    with db._db() as conn:
        conn.execute(query, args)
        conn.commit()


def test_verify_untouched_chain_is_ok(client, fake_label):
    cid = _three_events(client)
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": True}


def test_verify_empty_case_is_ok_and_missing_case_is_404(client):
    assert client.get(f"/api/cases/{new_case(client)['id']}/verify").json() == {"ok": True}
    assert client.get("/api/cases/case_9999/verify").status_code == 404


@pytest.mark.parametrize("tamper", [
    ("UPDATE events SET text = 'Sorry for the trouble' WHERE id = 'evt_0001'",),        # words changed
    ("UPDATE events SET at = '2026-11-13T11:40:00+05:30' WHERE id = 'evt_0001'",),      # 9:40 PM -> 11:40 AM
    ("UPDATE events SET rules = '[]' WHERE id = 'evt_0001'",),                          # rules removed
    ("DELETE FROM events WHERE id = 'evt_0002'",),                                      # an entry deleted
    ("UPDATE events SET seq = 99 WHERE id = 'evt_0001'",),                              # order changed
])
def test_verify_catches_any_hand_edit(client, fake_label, tamper):
    cid = _three_events(client)
    _sql(tamper[0])
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": False}


def test_verify_agrees_with_the_pdf_helper(client, fake_label):
    from api.core import evidence
    cid = _three_events(client)
    events = client.get(f"/api/cases/{cid}").json()["events"]
    assert main.chain_ok(events) is evidence.verify_chain(events) is True


# ---------------------------------------------------------------- F5 complaint route + day counter
from api.core import next_step as next_step_mod  # noqa: E402


@pytest.fixture
def rbi_list(monkeypatch, tmp_path):
    """A made-up RBI directory (no real company names)."""
    import dataclasses
    path = tmp_path / "rbi.csv"
    path.write_text("dla_name,regulated_entity,website,list_date\n"
                    "QuickRupee,Alpha Finance Pvt Ltd,https://quickrupee.in,2026-11-10\n", encoding="utf-8")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, rbi_dla_path=str(path)))


def case_for(client, lender_name, check_id=None):
    return client.post("/api/cases", json={"borrower_name": "Raju (test)", "lender_name": lender_name,
                                           "check_id": check_id}).json()


@pytest.mark.parametrize("match, expect", [
    ("FOUND", "grievance officer"), ("NOT_FOUND", "Sachet portal"), ("SIMILAR", "Check the exact app name"),
    (None, "Check the exact app name")])
def test_complaint_route_per_match(match, expect):
    route = next_step_mod.complaint_route(match)
    assert expect in route
    for word in ("illegal", "fake", "safe"):
        assert word not in route.lower()


def test_regulated_route_counts_the_30_days():
    assert next_step_mod.complaint_route("FOUND", 3).endswith("today is day 3 of 30.")
    assert "go to the RBI Ombudsman now" in next_step_mod.complaint_route("FOUND", 31)
    assert "day" not in next_step_mod.complaint_route("NOT_FOUND", 3)          # no 30-day wait there


def test_case_route_from_the_lender_name(client, rbi_list):
    assert "grievance officer" in case_for(client, "QuickRupee")["route"]
    assert "day 1 of 30" in case_for(client, "QuickRupee")["route"]
    assert "Sachet portal" in case_for(client, "ZapCash Express")["route"]


def test_case_route_without_an_rbi_list_is_unsure(client):
    # the real CSV on main is still only a header: "not checked" -> both routes, never "Sachet only"
    assert "Check the exact app name" in case_for(client, "QuickRupee")["route"]


def test_case_route_from_the_linked_check(client, rbi_list):
    db.save_check({"id": "chk_0042", "verdict": "VERY_COSTLY", "seconds": 4.0,
                   "numbers": {"extra": {"value": 1200, "status": "computed"}},
                   "lender": {"match": "NOT_FOUND"}}, None, "test")
    # the linked check said NOT_FOUND, even though this name would match the list
    assert "Sachet portal" in case_for(client, "QuickRupee", "chk_0042")["route"]


def test_pdf_prints_the_chosen_route(client, rbi_list, fake_label, monkeypatch):
    from api.core import evidence
    seen = {}
    real = evidence.build_pdf
    monkeypatch.setattr(evidence, "build_pdf", lambda case, **kw: (seen.update(case=case), real(case))[1])
    case = case_for(client, "ZapCash Express")
    log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna")
    client.get(f"/api/cases/{case['id']}/evidence.pdf")
    assert "Sachet portal" in seen["case"]["route"]
    lines = evidence.where_to_complain(seen["case"], {"H2": 1})
    assert len(lines) == 2 and "police" in lines[1]                      # the one route + police for threats
