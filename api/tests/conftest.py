import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def temp_database(monkeypatch, tmp_path):
    """Every test gets its own empty SQLite file (A3), so no test touches the real karzsamjho.db."""
    import dataclasses
    from api.core import config
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, db_path=str(tmp_path / "test.db")))
