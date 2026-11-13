"""The ONLY file that calls outside services (Groq, Gemini, edge-tts). Each call: temperature 0, a timeout, no retry on the same engine; on failure or a Groq 429 move to the next engine at once. Record engine name and seconds. Log usage tokens for every vision call. Never log keys.

Filled by task(s): A4, A6 in docs/TASKS.md. This is a skeleton: the signatures are a
starting point and may change inside the task, but the API contract may not.
"""


def read_image(image_bytes: bytes, prefer: str = "qwen") -> tuple[str, str, float]:
    raise NotImplementedError("read_image: see docs/TASKS.md A4, A6")


def read_text(prompt: str) -> tuple[str, str, float]:
    raise NotImplementedError("read_text: see docs/TASKS.md A4, A6")


async def speak(text: str, out_path: str) -> bool:
    raise NotImplementedError("speak: see docs/TASKS.md A4, A6")


def transcribe(audio_bytes: bytes) -> str:
    raise NotImplementedError("transcribe: see docs/TASKS.md A4, A6")
