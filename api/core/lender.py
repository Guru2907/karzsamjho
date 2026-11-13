"""RBI directory match with RapidFuzz WRatio against api/data/rbi_dla.csv. >= 90 FOUND, 70-89 SIMILAR, < 70 NOT_FOUND. Never say 'illegal' or 'fake'. Always return the list date.

Filled by task(s): C1, C3 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def match_lender(name: str | None) -> dict:
    raise NotImplementedError("match_lender: see docs/TASKS.md C1, C3")
