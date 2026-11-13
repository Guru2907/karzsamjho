"""Photo or text -> fields (through fallback.py). The AI only copies written numbers; it never calculates. Strip ```json fences, validate with Pydantic. Ignore an AI in_hand the ad did not state.

Filled by task(s): B1, B2, B6, B7 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def extract_from_image(image_bytes: bytes) -> dict:
    raise NotImplementedError("extract_from_image: see docs/TASKS.md B1, B2, B6, B7")


def extract_from_text(text: str) -> dict:
    raise NotImplementedError("extract_from_text: see docs/TASKS.md B1, B2, B6, B7")


def strip_fences(raw: str) -> str:
    raise NotImplementedError("strip_fences: see docs/TASKS.md B1, B2, B6, B7")
