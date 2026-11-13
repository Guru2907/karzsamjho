"""Smoke tests: the API starts and the contract shapes hold."""
from api.core.schemas import Case, CheckResult


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] == "up"
    # only true/false flags, never key values
    assert all(isinstance(body[k], bool) for k in ("groq_key", "gemini_key", "telegram_key"))


def test_post_check_with_image(client):
    r = client.post("/api/checks", files={"image": ("ad.jpg", b"\xff\xd8\xff\xd9", "image/jpeg")},
                    data={"lang": "hi", "source": "test"})
    assert r.status_code == 200
    CheckResult.model_validate(r.json())


def test_post_check_with_text(client):
    r = client.post("/api/checks", json={"text": "5000 ka loan, 7 din, 1200 fees"})
    assert r.status_code == 200
    CheckResult.model_validate(r.json())


def test_get_check_and_list(client):
    assert client.get("/api/checks/chk_0042").status_code == 200
    assert client.get("/api/checks/nope").status_code == 404
    assert len(client.get("/api/checks?limit=20").json()) >= 1


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
