"""The ONLY file that calls outside services (Groq, Gemini, edge-tts). Each call: temperature 0, a timeout, no retry on the same engine; on failure or a Groq 429 move to the next engine at once. Record engine name and seconds. Log usage tokens for every vision call. Never log keys.

Filled by task(s): A4, A6 in docs/TASKS.md. Signatures agreed in docs/PLAN.md.
Engine names used in results: "qwen", "gemini", "gpt-oss-20b", "edge-tts".
"""
import asyncio
import base64
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

import edge_tts
from google import genai
from google.genai import types as genai_types
from groq import Groq, RateLimitError

from api.core.config import settings

log = logging.getLogger("fallback")

Check = Callable[[str], Any]   # raises if the reply is not usable (e.g. invalid JSON)

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class EngineError(Exception):
    """Every engine that was tried has failed."""


# ---------------------------------------------------------------- helpers
def _mime(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"   # Telegram photos are JPEG


def _why(exc: Exception) -> str:
    """A short, safe reason for the log (type and HTTP status only, never the message)."""
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return f"{type(exc).__name__}{f' {status}' if status else ''}"


def _groq_chat(model: str, messages: list, timeout: float, **extra) -> tuple[str, dict]:
    """One Groq call, no retries. Returns (reply text, usage info for the log)."""
    client = Groq(api_key=settings.groq_api_key, timeout=timeout, max_retries=0)
    raw = client.chat.completions.with_raw_response.create(
        model=model, messages=messages, temperature=0, **extra)
    resp = raw.parse()
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "remaining_tokens": raw.headers.get("x-ratelimit-remaining-tokens"),
        "remaining_requests": raw.headers.get("x-ratelimit-remaining-requests"),
    }
    text = resp.choices[0].message.content or ""
    return _THINK.sub("", text).strip(), usage


# ---------------------------------------------------------------- engines
def _call_qwen(image_bytes: bytes, prompt: str) -> tuple[str, dict]:
    data_url = f"data:{_mime(image_bytes)};base64,{base64.b64encode(image_bytes).decode()}"
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]}]
    return _groq_chat(settings.groq_vision_model, messages, settings.vision_timeout_s)


def _call_gemini(image_bytes: bytes, prompt: str) -> tuple[str, dict]:
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=genai_types.HttpOptions(
            timeout=int(settings.read_timeout_s * 1000),          # milliseconds
            retry_options=genai_types.HttpRetryOptions(attempts=1)),
    )
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=[genai_types.Part.from_bytes(data=image_bytes, mime_type=_mime(image_bytes)), prompt],
        config=genai_types.GenerateContentConfig(temperature=0, response_mime_type="application/json"),
    )
    meta = resp.usage_metadata
    usage = {"prompt_tokens": getattr(meta, "prompt_token_count", None),
             "completion_tokens": getattr(meta, "candidates_token_count", None)}
    return (resp.text or "").strip(), usage


def _call_gpt_oss(prompt: str) -> tuple[str, dict]:
    messages = [{"role": "user", "content": prompt}]
    return _groq_chat(settings.groq_text_model, messages, settings.text_timeout_s,
                      reasoning_effort="low")


_IMAGE_ENGINES = {"qwen": ("_call_qwen", "groq_api_key"),
                  "gemini": ("_call_gemini", "gemini_api_key")}


# ---------------------------------------------------------------- public
def read_image(image_bytes: bytes, prompt: str, engines: tuple[str, ...] = ("qwen", "gemini"),
               check: Check | None = None) -> tuple[str, str, float]:
    """Photo -> (raw reply, engine name, seconds). Tries `engines` in order, once each.

    A timeout, any error, a Groq 429, or a reply that `check` rejects moves on to the
    next engine at once. Raises EngineError when every engine has failed.
    """
    for name in engines:
        fn_name, key_name = _IMAGE_ENGINES[name]
        if not getattr(settings, key_name):
            log.warning("read_image: engine=%s skipped (no key)", name)
            continue
        start = time.perf_counter()
        try:
            raw, usage = globals()[fn_name](image_bytes, prompt)
            if check:
                check(raw)
        except RateLimitError:
            log.warning("read_image: engine=%s 429 rate limit, moving on seconds=%.2f",
                        name, time.perf_counter() - start)
            continue
        except Exception as exc:
            log.warning("read_image: engine=%s failed (%s), moving on seconds=%.2f",
                        name, _why(exc), time.perf_counter() - start)
            continue
        seconds = round(time.perf_counter() - start, 2)
        log.info("read_image: engine=%s ok seconds=%.2f prompt_tokens=%s completion_tokens=%s "
                 "remaining_tokens=%s remaining_requests=%s", name, seconds,
                 usage.get("prompt_tokens"), usage.get("completion_tokens"),
                 usage.get("remaining_tokens"), usage.get("remaining_requests"))
        return raw, name, seconds
    raise EngineError(f"no reader answered (tried {', '.join(engines)})")


def read_text(prompt: str, check: Check | None = None) -> tuple[str, str, float]:
    """Text job -> (raw reply, "gpt-oss-20b", seconds). One engine; the caller's backup is regex.

    Raises EngineError on a timeout, any error, a 429, or a reply that `check` rejects.
    """
    if not settings.groq_api_key:
        raise EngineError("no Groq key")
    start = time.perf_counter()
    try:
        raw, usage = _call_gpt_oss(prompt)
        if check:
            check(raw)
    except Exception as exc:
        log.warning("read_text: engine=gpt-oss-20b failed (%s) seconds=%.2f",
                    _why(exc), time.perf_counter() - start)
        raise EngineError("text reader failed") from exc
    seconds = round(time.perf_counter() - start, 2)
    log.info("read_text: engine=gpt-oss-20b ok seconds=%.2f prompt_tokens=%s completion_tokens=%s "
             "remaining_tokens=%s", seconds, usage.get("prompt_tokens"),
             usage.get("completion_tokens"), usage.get("remaining_tokens"))
    return raw, "gpt-oss-20b", seconds


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


def transcribe(audio_bytes: bytes) -> tuple[str, str, float]:
    """Voice note (Telegram OGG) -> (Hindi transcript, "whisper", seconds). Task D6.

    One Groq Whisper call: language "hi", temperature 0, timeout from config, no retries.
    Raises EngineError on any failure, a 429, or an empty transcript (there is no second
    listener). Logs engine, seconds and the transcript LENGTH, never what was said.
    """
    if not settings.groq_api_key:
        raise EngineError("no Groq key")
    if not audio_bytes:
        raise EngineError("empty audio")
    start = time.perf_counter()
    try:
        client = Groq(api_key=settings.groq_api_key, timeout=settings.stt_timeout_s, max_retries=0)
        resp = client.audio.transcriptions.create(
            file=("voice.ogg", audio_bytes), model=settings.groq_stt_model,
            language="hi", temperature=0, response_format="json")
        text = (getattr(resp, "text", "") or "").strip()
        if not text:
            raise EngineError("whisper returned no text")
    except Exception as exc:
        log.warning("transcribe: engine=whisper failed (%s) seconds=%.2f",
                    _why(exc), time.perf_counter() - start)
        raise EngineError("listener failed") from exc
    seconds = round(time.perf_counter() - start, 2)
    log.info("transcribe: engine=whisper ok seconds=%.2f chars=%d", seconds, len(text))
    return text, "whisper", seconds
