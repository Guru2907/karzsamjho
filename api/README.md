# api/ (backend)

FastAPI + SQLite + Pydantic. All logic lives in `core/`.

- `main.py`: every route in the API contract (see CLAUDE.md). Right now each route returns sample data.
- `core/config.py`: model names, timeouts and thresholds, read from `.env`.
- `core/schemas.py`: the request and response shapes. Do not change without the whole team agreeing.
- `core/fallback.py`: the ONLY file that calls outside services. `core/db.py`: the ONLY file that opens the database.
- The other `core/` files are skeletons. Each one names the task that fills it.
- `data/`: RBI directory CSV and synthetic test data. `tests/`: pytest.

Run from the repo root: `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`. Test: `pytest -q`.
Tasks in docs/TASKS.md that touch this folder: A1-A6, B1-B7, C1-C3, D2, F1-F5, G1-G7.
