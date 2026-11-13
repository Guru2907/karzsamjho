"""Harassment rules H1-H6. H1 (time) and H6 (call count) are plain code. H2-H5 use the text model through fallback.py, with a keyword list as backup.

Filled by task(s): F1 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def label_event(event: dict, events_same_day: list[dict]) -> list[str]:
    raise NotImplementedError("label_event: see docs/TASKS.md F1")
