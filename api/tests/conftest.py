import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def offline_gemini_backups(monkeypatch):
    """B11: read_text and transcribe fall back to Gemini. In tests those backups are offline
    stand-ins that fail, so a test never reaches the internet; a test that wants Gemini to
    answer replaces them itself."""
    from api.core import fallback

    def offline(*args, **kwargs):
        raise fallback.EngineError("Gemini backup is offline in tests")
    monkeypatch.setattr(fallback, "_call_gemini_text", offline)
    monkeypatch.setattr(fallback, "_call_gemini_audio", offline)


@pytest.fixture(autouse=True)
def temp_database(monkeypatch, tmp_path):
    """Every test gets its own empty SQLite file (A3), so no test touches the real karzsamjho.db."""
    import dataclasses
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, db_path=str(tmp_path / "test.db")))


@pytest.fixture(autouse=True)
def offline_pings(monkeypatch):
    """/api/health pings Groq, Gemini and edge-tts (A5). Tests never touch the internet: the three
    pings are replaced by offline stand-ins that succeed, and the 60 s cache starts empty."""
    from api.core import fallback
    for name in ("_ping_groq", "_ping_gemini", "_ping_edge_tts"):
        monkeypatch.setattr(fallback, name, lambda: None)
    monkeypatch.setitem(fallback._ping_cache, "result", None)
