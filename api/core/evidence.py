"""Evidence PDF in ENGLISH (ReportLab) + hash chain + masking. hash = SHA-256(prev_hash + event fields). Mask any 12-digit number as XXXX XXXX 1234.

Filled by task(s): F2, F3, F4 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def event_hash(prev_hash: str, event: dict) -> str:
    raise NotImplementedError("event_hash: see docs/TASKS.md F2, F3, F4")


def verify_chain(events: list[dict]) -> bool:
    raise NotImplementedError("verify_chain: see docs/TASKS.md F2, F3, F4")


def mask_ids(text: str) -> str:
    raise NotImplementedError("mask_ids: see docs/TASKS.md F2, F3, F4")


def build_pdf(case: dict) -> bytes:
    raise NotImplementedError("build_pdf: see docs/TASKS.md F2, F3, F4")
