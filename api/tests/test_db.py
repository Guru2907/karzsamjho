"""db.py (A3): SQLite storage. Every test gets its own temp database file (conftest.py)."""
import dataclasses
import json

import pytest

from api import main
from api.core import config, db, fallback

RESULT = {"id": "chk_0007", "verdict": "VERY_COSTLY", "seconds": 3.9,
          "numbers": {"extra": {"value": 1200, "status": "computed"}},
          "engines": {"read": "qwen"}}


# ---------------------------------------------------------------- checks
def test_save_and_read_back_a_check():
    db.save_check(RESULT, "ab" * 32, "telegram")
    assert db.get_check("chk_0007") == RESULT
    assert db.get_check("chk_9999") is None
    assert db.list_checks() == [RESULT]
    assert db.check_summaries() == [{"verdict": "VERY_COSTLY", "extra": 1200, "seconds": 3.9}]
    assert db.max_check_number() == 7


def test_cache_hit_does_not_overwrite_the_first_answer():
    db.save_check(RESULT, None, "telegram")
    db.save_check({**RESULT, "verdict": "USUAL"}, None, "cache", replace=False)
    assert db.get_check("chk_0007")["verdict"] == "VERY_COSTLY"


def test_list_checks_newest_first_and_limit():
    for n in (1, 2, 3):
        db.save_check({**RESULT, "id": f"chk_000{n}"}, None, "web")
    assert [c["id"] for c in db.list_checks()] == ["chk_0003", "chk_0002", "chk_0001"]
    assert len(db.list_checks(limit=2)) == 2


def test_survives_a_new_connection_same_file(tmp_path, monkeypatch):
    path = str(tmp_path / "persist.db")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, db_path=path))
    db.save_check(RESULT, None, "telegram")
    db._ready.discard(path)                           # like a fresh process opening the same file
    assert db.get_check("chk_0007") == RESULT


# ---------------------------------------------------------------- cases and events
def event(at, channel="call", text="Paisa do", h="1" * 64, prev=db.GENESIS_HASH, rules=("H1",)):
    return {"at": at, "channel": channel, "contacted": "borrower", "text": text,
            "rules": list(rules), "hash": h, "prev_hash": prev}


def test_case_with_events_in_order():
    case = db.create_case("Raju (sample)", "QuickCash", "chk_0007")
    assert case["id"] == "case_0001" and case["events"] == [] and case["check_id"] == "chk_0007"
    assert db.last_event_hash("case_0001") == db.GENESIS_HASH          # F2 starts the chain here
    first = db.add_event("case_0001", event("2026-11-13T21:40:00+05:30"))
    second = db.add_event("case_0001", event("2026-11-14T10:15:00+05:30", channel="whatsapp",
                                             h="2" * 64, prev="1" * 64, rules=("H3",)))
    assert (first["id"], second["id"]) == ("evt_0001", "evt_0002")
    stored = db.get_case("case_0001")
    assert [e["id"] for e in stored["events"]] == ["evt_0001", "evt_0002"]
    assert stored["events"][1]["rules"] == ["H3"] and stored["events"][1]["prev_hash"] == "1" * 64
    assert db.last_event_hash("case_0001") == "2" * 64
    assert db.create_case("Raju 2", "FastLoan", None)["id"] == "case_0002"
    assert [c["id"] for c in db.list_cases()][0] == "case_0002"            # newest first


def test_event_for_a_missing_case_is_refused():
    with pytest.raises(KeyError):
        db.add_event("case_9999", event("2026-11-13T21:40:00+05:30"))


def test_calls_on_a_day_for_h6():
    db.create_case("Raju", "QuickCash", None)
    for hour in (9, 10, 11, 12, 13):
        db.add_event("case_0001", event(f"2026-11-13T{hour:02d}:00:00+05:30"))
    db.add_event("case_0001", event("2026-11-13T14:00:00+05:30", channel="sms"))
    db.add_event("case_0001", event("2026-11-14T09:00:00+05:30"))
    assert db.calls_on("case_0001", "2026-11-13") == 5         # SMS and next day not counted
    assert db.calls_on("case_0001", "2026-11-14") == 1
    assert db.calls_on("case_0001", "2026-11-15") == 0


# ---------------------------------------------------------------- through the API: a restart
@pytest.fixture
def api_env(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})

    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "principal": 5000, "fees": 500,
                           "repay_total": 5600, "tenure_days": 7}), "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "read_text", read_text)


def test_check_survives_an_api_restart(client, api_env, monkeypatch):
    sms = "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days."
    first = client.post("/api/checks", json={"text": sms, "source": "telegram"}).json()
    monkeypatch.setattr(main, "CHECKS", {})               # what a restart loses
    monkeypatch.setattr(main, "_ids", None)               # the counter starts again too
    again = client.get(f"/api/checks/{first['id']}")
    assert again.status_code == 200 and again.json()["numbers"] == first["numbers"]
    assert [c["id"] for c in client.get("/api/checks").json()] == [first["id"]]
    second = client.post("/api/checks", json={"text": sms}).json()
    assert int(second["id"][4:]) == int(first["id"][4:]) + 1      # id never reused after a restart
    stats = client.get("/api/stats").json()
    assert stats["checks"] == 2 and stats["extra_rupees_flagged"] == 2200
    assert client.get("/api/health").json()["checks_stored"] == 2
