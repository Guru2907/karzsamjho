"""A5: /api/health shows each engine up or down (offline stand-ins, no internet)."""
import dataclasses

import httpx
import pytest
from groq import RateLimitError

from api.core import config, db, fallback


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(
        fallback.settings, groq_api_key="fake-groq", gemini_api_key="fake-gemini"))


def fail(exc):
    def f():
        raise exc
    return f


def rate_limited():
    return RateLimitError("429", response=httpx.Response(429, request=httpx.Request("GET", "https://x")), body=None)


def test_all_up(client, keys):
    h = client.get("/api/health").json()
    assert {k: v["up"] for k, v in h["engines"].items()} == {"groq": True, "gemini": True, "edge-tts": True}
    assert h["can_read_photos"] is True and h["database"] == "up"


def test_groq_rate_limited_gemini_still_reads_photos(client, keys, monkeypatch):
    monkeypatch.setattr(fallback, "_ping_groq", fail(rate_limited()))
    h = client.get("/api/health").json()
    assert h["engines"]["groq"] == {"up": False, "why": "RateLimitError 429", "seconds": h["engines"]["groq"]["seconds"]}
    assert h["engines"]["gemini"]["up"] is True and h["can_read_photos"] is True


def test_both_readers_down(client, keys, monkeypatch):
    monkeypatch.setattr(fallback, "_ping_groq", fail(TimeoutError()))
    monkeypatch.setattr(fallback, "_ping_gemini", fail(ConnectionError()))
    assert client.get("/api/health").json()["can_read_photos"] is False


def test_no_key_is_down_without_calling(client, monkeypatch):
    called = []
    monkeypatch.setattr(fallback, "settings", dataclasses.replace(fallback.settings, groq_api_key=""))
    monkeypatch.setattr(fallback, "_ping_groq", lambda: called.append(1))
    assert client.get("/api/health").json()["engines"]["groq"] == {"up": False, "why": "no key"}
    assert called == []


def test_voice_down(client, keys, monkeypatch):
    monkeypatch.setattr(fallback, "_ping_edge_tts", fail(OSError()))
    h = client.get("/api/health").json()
    assert h["engines"]["edge-tts"]["up"] is False and h["can_speak"] is False


def test_pings_are_cached_and_fresh_rechecks(client, keys, monkeypatch):
    calls = []
    monkeypatch.setattr(fallback, "_ping_groq", lambda: calls.append(1))
    client.get("/api/health"); client.get("/api/health")
    assert len(calls) == 1                                   # second call used the 60 s cache
    client.get("/api/health?fresh=true")
    assert len(calls) == 2


def test_health_never_shows_key_values(client, keys):
    body = client.get("/api/health").text
    assert "fake-groq" not in body and "fake-gemini" not in body


def test_broken_database_does_not_take_health_down(client, keys, monkeypatch):
    monkeypatch.setattr(db, "check_summaries", fail(OSError("disk")))
    h = client.get("/api/health").json()
    assert h["api"] == "up" and h["database"].startswith("down") and h["checks_stored"] is None


def test_stats_match_the_database(client):
    for n, (verdict, extra, secs) in enumerate([("VERY_COSTLY", 1200, 3.0), ("USUAL", 250, 5.0),
                                                ("COSTLY", 600, 4.0)], 1):
        db.save_check({"id": f"chk_{n:04d}", "verdict": verdict, "seconds": secs,
                       "numbers": {"extra": {"value": extra, "status": "computed"}}}, None, "test")
    assert client.get("/api/stats").json() == {"checks": 3, "median_seconds": 4.0, "extra_rupees_flagged": 1800}
