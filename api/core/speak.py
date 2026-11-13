"""Fixed Hindi sentence template filled by code (never AI-written) + audio through fallback.py (edge-tts). If audio fails, return None and the card is sent alone.

Filled by task(s): D2 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def speech_text(numbers: dict) -> str:
    raise NotImplementedError("speech_text: see docs/TASKS.md D2")


async def make_audio(check_id: str, text: str) -> str | None:
    raise NotImplementedError("make_audio: see docs/TASKS.md D2")
