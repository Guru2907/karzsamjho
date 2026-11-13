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
    case = client.post("/api/cases", json={"borrower_name": "Raju (test)", "lender_name": "QuickCash"}).json()
    Case.model_validate(case)
    r = client.post(f"/api/cases/{case['id']}/events",
                    json={"at": "2026-11-13T21:40:00+05:30", "channel": "call",
                          "contacted": "borrower", "text": "sample"})
    assert r.status_code == 200 and len(r.json()["hash"]) == 64
    Case.model_validate(client.get("/api/cases").json()[0])


def test_stats(client):
    assert set(client.get("/api/stats").json()) == {"checks", "median_seconds", "extra_rupees_flagged"}
