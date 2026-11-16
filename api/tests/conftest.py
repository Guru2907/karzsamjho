import os

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
def temp_database(monkeypatch, tmp_path, request):
    """Every test gets its own empty SQLite file (A3), so no test touches the real karzsamjho.db,
    and DATABASE_URL is blanked, so no test ever writes to the real Postgres (Neon) database (D58).
    With KS_TEST_DATABASE_URL set, the whole suite runs on Postgres instead, in a throw-away schema
    that is emptied before every test (see pg_test_url below)."""
    import dataclasses
    from api.core import config, db
    pg = request.getfixturevalue("pg_test_url") if os.getenv("KS_TEST_DATABASE_URL") else ""
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, db_path=str(tmp_path / "test.db"), database_url=pg))
    if pg:
        with db._db() as conn:
            conn.execute("TRUNCATE photos, events, cases, checks, chats")


@pytest.fixture(scope="session")
def pg_test_url():
    """KS_TEST_DATABASE_URL (a Postgres URL, e.g. Neon's direct, non-pooled one) -> a URL that puts
    every table in a new schema test_<random>, dropped again when the run ends. The real tables
    in the public schema are never touched."""
    import secrets
    from urllib.parse import quote
    import psycopg
    base = os.environ["KS_TEST_DATABASE_URL"]
    schema = "test_" + secrets.token_hex(4)
    with psycopg.connect(base, autocommit=True) as conn:
        conn.execute(f"CREATE SCHEMA {schema}")
    sep = "&" if "?" in base else "?"
    yield f"{base}{sep}options={quote(f'-c search_path={schema}')}"
    from api.core import db
    db.close_pools()
    with psycopg.connect(base, autocommit=True) as conn:
        conn.execute(f"DROP SCHEMA {schema} CASCADE")


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
                        dataclasses.replace(config.settings, rbi_dla_path=str(_empty_rbi_csv),
                                            rbi_nbfc_path=str(_empty_rbi_csv.with_name("no_nbfc_list.csv")),
                                            watch_list_path=str(_empty_rbi_csv.with_name("no_watch_list.csv"))))


@pytest.fixture(autouse=True)
def offline_pings(monkeypatch):
    """/api/health pings Groq, Gemini and edge-tts (A5). Tests never touch the internet: the three
    pings are replaced by offline stand-ins that succeed, and the 60 s cache starts empty."""
    from api.core import fallback
    for name in ("_ping_groq", "_ping_gemini", "_ping_edge_tts"):
        monkeypatch.setattr(fallback, name, lambda: None)
    monkeypatch.setitem(fallback._ping_cache, "result", None)
