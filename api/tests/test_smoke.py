"""Smoke tests: the API starts and the contract shapes hold (cases are still sample data)."""
from api.core.schemas import Case


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] == "up"
    # only true/false flags, never key values
    assert all(isinstance(body[k], bool) for k in ("groq_key", "gemini_key", "telegram_key"))


# Check tests (photo, text, get, list, audio) live in test_pipeline.py: checks are real now.


def test_cases(client):
    cases = client.get("/api/cases").json()
    Case.model_validate(cases[0])
    r = client.post("/api/cases/case_0007/events",
                    json={"at": "2026-11-13T21:40:00+05:30", "channel": "call",
                          "contacted": "borrower", "text": "sample"})
    assert r.status_code == 200 and "hash" in r.json()
    assert client.get("/api/cases/case_0007/verify").json() == {"ok": True}


def test_stats(client):
    assert set(client.get("/api/stats").json()) == {"checks", "median_seconds", "extra_rupees_flagged"}
