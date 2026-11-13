"""The ONLY file that calls outside services (Groq, Gemini, edge-tts). Each call: temperature 0, a timeout, no retry on the same engine; on failure or a Groq 429 move to the next engine at once. Record engine name and seconds. Log usage tokens for every vision call. Never log keys.

Filled by task(s): A4, A6 in docs/TASKS.md. Signatures agreed in docs/PLAN.md.
Done so far: speak() (L1). read_image() and read_text() come next (L2).
"""
import asyncio
import logging
import os
import time
from pathlib import Path

import edge_tts

from api.core.config import settings

log = logging.getLogger("fallback")


class EngineError(Exception):
    """Every engine that was tried has failed."""


def read_image(image_bytes: bytes, engines: tuple[str, ...] = ("qwen", "gemini")) -> tuple[str, str, float]:
    raise NotImplementedError("read_image: see docs/PLAN.md L2")


def read_text(prompt: str) -> tuple[str, str, float]:
    raise NotImplementedError("read_text: see docs/PLAN.md L2")


async def speak(text: str, out_path: str) -> bool:
    """Hindi text -> MP3 at out_path with edge-tts. True only if a non-empty MP3 was written.

    Never raises: on a timeout or any failure it returns False, so the card is sent alone.
    Writes to a .part file first and renames it, so a half-written MP3 is never served.
    """
    if not text or not text.strip():
        return False
    out = Path(out_path)
    part = out.with_name(out.name + ".part")
    start = time.perf_counter()
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        tts = edge_tts.Communicate(text, settings.tts_voice_hi)
        await asyncio.wait_for(tts.save(str(part)), timeout=settings.tts_timeout_s)
        if not part.exists() or part.stat().st_size == 0:
            raise EngineError("edge-tts wrote no audio")
        os.replace(part, out)
    except Exception as exc:  # timeout, network, empty audio: all mean "no voice"
        log.warning("speak failed: engine=edge-tts seconds=%.2f error=%s",
                    time.perf_counter() - start, type(exc).__name__)
        part.unlink(missing_ok=True)
        return False
    log.info("speak ok: engine=edge-tts seconds=%.2f bytes=%d",
             time.perf_counter() - start, out.stat().st_size)
    return True


def transcribe(audio_bytes: bytes) -> str:
    raise NotImplementedError("transcribe: stretch task D6")
