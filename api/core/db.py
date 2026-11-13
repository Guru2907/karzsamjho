"""ALL SQLite access. Tables: checks, cases, events (see docs/ARCHITECTURE.md). No other file opens the database.

Filled by task(s): A3 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def init_db() -> None:
    raise NotImplementedError("init_db: see docs/TASKS.md A3")


def save_check(result: dict, image_sha256: str | None, source: str) -> None:
    raise NotImplementedError("save_check: see docs/TASKS.md A3")


def get_check(check_id: str) -> dict | None:
    raise NotImplementedError("get_check: see docs/TASKS.md A3")


def list_checks(limit: int = 20) -> list[dict]:
    raise NotImplementedError("list_checks: see docs/TASKS.md A3")


def create_case(borrower_name: str, lender_name: str, check_id: str | None) -> dict:
    raise NotImplementedError("create_case: see docs/TASKS.md A3")


def add_event(case_id: str, event: dict) -> dict:
    raise NotImplementedError("add_event: see docs/TASKS.md A3")


def get_case(case_id: str) -> dict | None:
    raise NotImplementedError("get_case: see docs/TASKS.md A3")


def list_cases() -> list[dict]:
    raise NotImplementedError("list_cases: see docs/TASKS.md A3")
