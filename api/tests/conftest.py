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

