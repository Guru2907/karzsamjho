"""Rupee maths in plain Python. extra, cost_pct, per_day, per_week_pct, apr_simple; cross-check within Rs 1; fill gaps only from numbers that were read. A missing input makes every dependent output 'unverified'. tenure_days <= 0 is 'unverified', never a division error.

Filled by task(s): B3, B4 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def cross_check(fields: dict) -> list[str]:
    raise NotImplementedError("cross_check: see docs/TASKS.md B3, B4")


def fill_gaps(fields: dict) -> dict:
    raise NotImplementedError("fill_gaps: see docs/TASKS.md B3, B4")


def compute(fields: dict) -> dict:
    raise NotImplementedError("compute: see docs/TASKS.md B3, B4")
