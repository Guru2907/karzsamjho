"""ALL SQLite access (task A3). Tables: checks, cases, events (docs/ARCHITECTURE.md). No other file opens the database.

The file is config.settings.db_path (DB_PATH in .env, default ./karzsamjho.db; *.db is in .gitignore).
Each call opens a short connection, so the API's worker threads never share one.
Hashes are worked out by the caller (F2); this file only stores and reads them.
"""
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api.core import config

IST = timezone(timedelta(hours=5, minutes=30))
GENESIS_HASH = "0" * 64              # prev_hash of a case's first event

_SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id           TEXT PRIMARY KEY,
    created_at   TEXT NOT NULL,
    source       TEXT,
    image_sha256 TEXT,
    verdict      TEXT,
    extra        REAL,
    seconds      REAL,
    engines      TEXT,
    result_json  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cases (
    id            TEXT PRIMARY KEY,
    borrower_name TEXT NOT NULL,
    lender_name   TEXT NOT NULL,
    check_id      TEXT,
    route         TEXT,
    opened_at     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    id         TEXT UNIQUE NOT NULL,
    case_id    TEXT NOT NULL REFERENCES cases(id),
    at         TEXT NOT NULL,
    channel    TEXT,
    contacted  TEXT,
    text       TEXT,
    rules      TEXT NOT NULL,
    hash       TEXT NOT NULL,
    prev_hash  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS events_by_case ON events(case_id, seq);
"""
_ready: set[str] = set()             # database paths whose tables already exist


def now_ist() -> str:
    return datetime.now(IST).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    path = config.settings.db_path
    if path not in _ready:
        init_db()
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tables if they are missing. Safe to call any number of times."""
    path = config.settings.db_path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=10)) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()
    _ready.add(path)


# ---------------------------------------------------------------- checks
def save_check(result: dict, image_sha256: str | None, source: str, replace: bool = True) -> None:
    """Store a CheckResult. replace=False keeps an existing row (used for cache hits)."""
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    extra = (result.get("numbers", {}).get("extra") or {}).get("value")
    with closing(_connect()) as conn:
        conn.execute(
            f"{verb} INTO checks (id, created_at, source, image_sha256, verdict, extra, seconds, "
            "engines, result_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (result["id"], now_ist(), source, image_sha256, result.get("verdict"), extra,
             result.get("seconds"), json.dumps(result.get("engines") or {}),
             json.dumps(result, ensure_ascii=False)))
        conn.commit()


def get_check(check_id: str) -> dict | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT result_json FROM checks WHERE id = ?", (check_id,)).fetchone()
    return json.loads(row["result_json"]) if row else None


def list_checks(limit: int = 20) -> list[dict]:
    """Newest first."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT result_json FROM checks ORDER BY created_at DESC, id DESC LIMIT ?",
                            (max(int(limit), 0),)).fetchall()
    return [json.loads(r["result_json"]) for r in rows]


def check_summaries() -> list[dict]:
    """verdict, extra and seconds of every stored check (for /api/stats)."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT verdict, extra, seconds FROM checks").fetchall()
    return [dict(r) for r in rows]


def max_check_number() -> int:
    """Highest N in a stored id chk_NNNN (0 if none), so new ids never repeat."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT id FROM checks WHERE id LIKE 'chk_%'").fetchall()
    numbers = [int(r["id"][4:]) for r in rows if r["id"][4:].isdigit()]
    return max(numbers, default=0)


# ---------------------------------------------------------------- cases and events
def _next_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    rows = conn.execute(f"SELECT id FROM {table} WHERE id LIKE ?", (prefix + "%",)).fetchall()
    numbers = [int(r["id"][len(prefix):]) for r in rows if r["id"][len(prefix):].isdigit()]
    return f"{prefix}{max(numbers, default=0) + 1:04d}"


def create_case(borrower_name: str, lender_name: str, check_id: str | None,
                route: str | None = None) -> dict:
    with closing(_connect()) as conn:
        case_id = _next_id(conn, "cases", "case_")
        conn.execute("INSERT INTO cases (id, borrower_name, lender_name, check_id, route, opened_at) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (case_id, borrower_name, lender_name, check_id, route, now_ist()))
        conn.commit()
    return get_case(case_id)


def add_event(case_id: str, event: dict) -> dict:
    """Store one event exactly as given: at, channel, contacted, text, rules, hash, prev_hash.

    The caller (F2) works out rules and hash; this only stores them, in order.
    """
    with closing(_connect()) as conn:
        if not conn.execute("SELECT 1 FROM cases WHERE id = ?", (case_id,)).fetchone():
            raise KeyError(case_id)
        event_id = _next_id(conn, "events", "evt_")
        conn.execute("INSERT INTO events (id, case_id, at, channel, contacted, text, rules, hash, prev_hash) "
                     "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                     (event_id, case_id, event["at"], event.get("channel"), event.get("contacted"),
                      event.get("text", ""), json.dumps(list(event.get("rules") or [])),
                      event["hash"], event["prev_hash"]))
        conn.commit()
    return {"id": event_id, "at": event["at"], "channel": event.get("channel"),
            "contacted": event.get("contacted"), "text": event.get("text", ""),
            "rules": list(event.get("rules") or []), "hash": event["hash"], "prev_hash": event["prev_hash"]}


def _events(conn: sqlite3.Connection, case_id: str) -> list[dict]:
    rows = conn.execute("SELECT id, at, channel, contacted, text, rules, hash, prev_hash FROM events "
                        "WHERE case_id = ? ORDER BY seq", (case_id,)).fetchall()
    return [{**dict(r), "rules": json.loads(r["rules"])} for r in rows]


def get_case(case_id: str) -> dict | None:
    """The case with its events in the order they were logged (day counter is added by the caller)."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return None
        return {**dict(row), "events": _events(conn, case_id)}


def list_cases() -> list[dict]:
    """Newest case first, each with its events."""
    with closing(_connect()) as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY opened_at DESC, id DESC").fetchall()
        return [{**dict(r), "events": _events(conn, r["id"])} for r in rows]


def last_event_hash(case_id: str) -> str:
    """Hash of the case's latest event, or GENESIS_HASH for its first one (F2 chains on this)."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT hash FROM events WHERE case_id = ? ORDER BY seq DESC LIMIT 1",
                           (case_id,)).fetchone()
    return row["hash"] if row else GENESIS_HASH


def calls_on(case_id: str, date: str) -> int:
    """How many call events this case has on a date (YYYY-MM-DD, from the event's own time). For H6."""
    with closing(_connect()) as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM events WHERE case_id = ? AND channel = 'call' "
                           "AND substr(at, 1, 10) = ?", (case_id, date)).fetchone()
    return int(row["n"])
