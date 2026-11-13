"""Results stored by SHA-256 of the image bytes. A hit returns the stored result and audio and never calls an AI service.

Filled by task(s): A4 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def image_key(image_bytes: bytes) -> str:
    raise NotImplementedError("image_key: see docs/TASKS.md A4")


def get(key: str) -> dict | None:
    raise NotImplementedError("get: see docs/TASKS.md A4")


def put(key: str, result: dict) -> None:
    raise NotImplementedError("put: see docs/TASKS.md A4")
