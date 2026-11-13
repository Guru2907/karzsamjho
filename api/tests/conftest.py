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


@pytest.fixture(scope="session")
def _empty_rbi_csv(tmp_path_factory):
    """One header-only RBI directory file for the whole run, outside every test's own tmp_path
    (some tests check that their tmp_path stays empty)."""
    path = tmp_path_factory.mktemp("rbi") / "rbi_dla_empty.csv"
    path.write_text("dla_name,regulated_entity,website,list_date\n", encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def empty_rbi_list(monkeypatch, _empty_rbi_csv):
    """Every test starts with an EMPTY RBI directory (lender match = null, "not checked"), so tests about
    maths, voice or cases do not change when api/data/rbi_dla.csv (RBI's real list, G4) is updated.
    A test that needs a list points rbi_dla_path at its own file (or at the real one, see test_lender.py)."""
    import dataclasses
    from api.core import config
    monkeypatch.setattr(config, "settings",
                        dataclasses.replace(config.settings, rbi_dla_path=str(_empty_rbi_csv)))


@pytest.fixture(autouse=True)
def offline_pings(monkeypatch):
    """/api/health pings Groq, Gemini and edge-tts (A5). Tests never touch the internet: the three
    pings are replaced by offline stand-ins that succeed, and the 60 s cache starts empty."""
    from api.core import fallback
    for name in ("_ping_groq", "_ping_gemini", "_ping_edge_tts"):
        monkeypatch.setattr(fallback, name, lambda: None)
    monkeypatch.setitem(fallback._ping_cache, "result", None)
