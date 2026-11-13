"""F2: real cases + events with a hash chain (A3 database). No internet; harass.label is faked."""
import hashlib
import json
import sqlite3
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
    assert case["id"] == "case_0001" and case["events"] == [] and case["day"] == 1
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
    with sqlite3.connect(config.settings.db_path) as conn:                  # pretend it opened 3 days ago
        when = (datetime.now(db.IST) - timedelta(days=3)).isoformat(timespec="seconds")
        conn.execute("UPDATE cases SET opened_at = ? WHERE id = ?", (when, case["id"]))
    assert client.get(f"/api/cases/{case['id']}").json()["day"] == 4


def test_chain_survives_a_restart(client, fake_label, monkeypatch):
    case = new_case(client)
    first = log_event(client, case["id"], "2026-11-13T21:40:00+05:30", "Paisa do warna").json()
    db._ready.clear()                                                       # a fresh process
    second = log_event(client, case["id"], "2026-11-13T22:00:00+05:30").json()
    assert second["prev_hash"] == first["hash"]
    events = client.get(f"/api/cases/{case['id']}").json()["events"]
    assert all(main.event_hash(e["prev_hash"], e) == e["hash"] for e in events)


def test_list_cases_newest_first(client):
    new_case(client)
    second = new_case(client)
    assert client.get("/api/cases").json()[0]["id"] == second["id"]


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
