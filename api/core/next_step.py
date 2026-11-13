"""Verdict + lender match -> exactly one next action, and the complaint route for a case.

Filled by task(s): C2, F5 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def next_step(verdict: str, lender_match: str) -> dict:
    raise NotImplementedError("next_step: see docs/TASKS.md C2, F5")


def complaint_route(lender_match: str, has_threats: bool) -> str:
    raise NotImplementedError("complaint_route: see docs/TASKS.md C2, F5")
