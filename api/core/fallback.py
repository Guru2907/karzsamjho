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


def _gemini_client(timeout_s: float):
    return genai.Client(api_key=settings.gemini_api_key, http_options=genai_types.HttpOptions(
        timeout=int(timeout_s * 1000), retry_options=genai_types.HttpRetryOptions(attempts=1)))


def _call_gemini_text(prompt: str) -> tuple[str, dict]:
    """Text job on Gemini Flash-Lite: the backup when Groq gpt-oss fails (B11)."""
    client = _gemini_client(settings.read_timeout_s)       # keep a reference: a dropped client closes
    resp = client.models.generate_content(
        model=settings.gemini_model, contents=[prompt],
        config=genai_types.GenerateContentConfig(temperature=0))
    meta = resp.usage_metadata
    return (resp.text or "").strip(), {"prompt_tokens": getattr(meta, "prompt_token_count", None),
                                       "completion_tokens": getattr(meta, "candidates_token_count", None)}


_TEXT_ENGINES = {"gpt-oss-20b": ("_call_gpt_oss", "groq_api_key"),
                 "gemini": ("_call_gemini_text", "gemini_api_key")}


def read_text(prompt: str, check: Check | None = None,
              engines: tuple[str, ...] = ("gpt-oss-20b", "gemini")) -> tuple[str, str, float]:
    """Text job -> (raw reply, engine name, seconds). gpt-oss-20b first, Gemini Flash-Lite if it fails
    (B11); each once, temperature 0, a timeout, no retry; a 429 or a reply `check` rejects moves on.
    Raises EngineError when every engine failed (the caller's last resort is then regex)."""
    for name in engines:
        fn_name, key_name = _TEXT_ENGINES[name]
        if not getattr(settings, key_name):
            log.warning("read_text: engine=%s skipped (no key)", name)
            continue
        start = time.perf_counter()
        try:
            raw, usage = globals()[fn_name](prompt)
            if check:
                check(raw)
        except Exception as exc:
            log.warning("read_text: engine=%s failed (%s), moving on seconds=%.2f",
                        name, _why(exc), time.perf_counter() - start)
            continue
        seconds = round(time.perf_counter() - start, 2)
        log.info("read_text: engine=%s ok seconds=%.2f prompt_tokens=%s completion_tokens=%s "
                 "remaining_tokens=%s", name, seconds, usage.get("prompt_tokens"),
                 usage.get("completion_tokens"), usage.get("remaining_tokens"))
        return raw, name, seconds
    raise EngineError(f"no text reader answered (tried {', '.join(engines)})")


async def speak(text: str, out_path: str, voice: str | None = None) -> bool:
    """Text -> MP3 at out_path with edge-tts. True only if a non-empty MP3 was written.

    voice: an edge-tts voice name (D7: bn-IN-TanishaaNeural, mr-IN-AarohiNeural);
    None means the Hindi voice from config.

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
        tts = edge_tts.Communicate(text, voice or settings.tts_voice_hi)
        await asyncio.wait_for(tts.save(str(part)), timeout=settings.tts_timeout_s)
        if not part.exists() or part.stat().st_size == 0:
            raise EngineError("edge-tts wrote no audio")
        os.replace(part, out)
    except Exception as exc:  # timeout, network, empty audio: all mean "no voice"
        log.warning("speak failed: engine=edge-tts seconds=%.2f error=%s",
                    time.perf_counter() - start, type(exc).__name__)
        part.unlink(missing_ok=True)
        return False
    log.info("speak ok: engine=edge-tts voice=%s seconds=%.2f bytes=%d",
             voice or settings.tts_voice_hi, time.perf_counter() - start, out.stat().st_size)
    return True


def _audio_mime(audio_bytes: bytes) -> str:
    if audio_bytes[:4] == b"OggS":
        return "audio/ogg"                        # Telegram voice notes
    if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return "audio/wav"
    return "audio/mpeg"


def _call_whisper(audio_bytes: bytes) -> str:
    client = Groq(api_key=settings.groq_api_key, timeout=settings.stt_timeout_s, max_retries=0)
    resp = client.audio.transcriptions.create(
        file=("voice.ogg", audio_bytes), model=settings.groq_stt_model,
        language="hi", temperature=0, response_format="json")
    return (getattr(resp, "text", "") or "").strip()


def _call_gemini_audio(audio_bytes: bytes) -> str:
    """Gemini Flash-Lite listens to the voice note: the backup when Whisper fails (B11).
    Tested 13 Nov 8 PM: Hindi speech in 2.4 to 3.1 s, numbers written as digits."""
    client = _gemini_client(settings.read_timeout_s)       # keep a reference: a dropped client closes
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=[genai_types.Part.from_bytes(data=audio_bytes, mime_type=_audio_mime(audio_bytes)),
                  "Write down exactly what is said in this audio, in the language spoken. "
                  "Output only the words, nothing else."],
        config=genai_types.GenerateContentConfig(temperature=0))
    return (resp.text or "").strip()


_LISTENERS = {"whisper": ("_call_whisper", "groq_api_key"),
              "gemini": ("_call_gemini_audio", "gemini_api_key")}


def transcribe(audio_bytes: bytes) -> tuple[str, str, float]:
    """Voice note (Telegram OGG) -> (transcript, engine, seconds). Task D6; Gemini backup B11.

    Whisper first (language "hi"), then Gemini Flash-Lite; each once, temperature 0, a timeout,
    no retries; a 429, an error or an empty transcript moves on. Raises EngineError when both fail.
    Logs engine, seconds and the transcript LENGTH, never what was said.
    """
    if not audio_bytes:
        raise EngineError("empty audio")
    for name, (fn_name, key_name) in _LISTENERS.items():
        if not getattr(settings, key_name):
            log.warning("transcribe: engine=%s skipped (no key)", name)
            continue
        start = time.perf_counter()
        try:
            text = globals()[fn_name](audio_bytes)
            if not text:
                raise EngineError(f"{name} returned no text")
        except Exception as exc:
            log.warning("transcribe: engine=%s failed (%s), moving on seconds=%.2f",
                        name, _why(exc), time.perf_counter() - start)
            continue
        seconds = round(time.perf_counter() - start, 2)
        log.info("transcribe: engine=%s ok seconds=%.2f chars=%d", name, seconds, len(text))
        return text, name, seconds
    raise EngineError("listener failed (tried whisper, gemini)")


# ---------------------------------------------------------------- health pings (A5)
PING_TIMEOUT_S = 4.0
PING_CACHE_S = 60.0
_ping_cache: dict = {"at": 0.0, "result": None}


def _ping_groq() -> None:
    Groq(api_key=settings.groq_api_key, timeout=PING_TIMEOUT_S, max_retries=0).models.list()


def _ping_gemini() -> None:
    client = genai.Client(api_key=settings.gemini_api_key, http_options=genai_types.HttpOptions(
        timeout=int(PING_TIMEOUT_S * 1000), retry_options=genai_types.HttpRetryOptions(attempts=1)))
    client.models.get(model=settings.gemini_model)


def _ping_edge_tts() -> None:
    asyncio.run(asyncio.wait_for(edge_tts.list_voices(), timeout=PING_TIMEOUT_S))


_PINGS = {"groq": ("_ping_groq", "groq_api_key"), "gemini": ("_ping_gemini", "gemini_api_key"),
          "edge-tts": ("_ping_edge_tts", None)}


def _one_ping(name: str) -> dict:
    fn_name, key_name = _PINGS[name]
    if key_name and not getattr(settings, key_name):
        return {"up": False, "why": "no key"}
    start = time.perf_counter()
    try:
        globals()[fn_name]()
    except Exception as exc:
        return {"up": False, "why": _why(exc), "seconds": round(time.perf_counter() - start, 2)}
    return {"up": True, "seconds": round(time.perf_counter() - start, 2)}


def ping(force: bool = False) -> dict:
    """Is each outside engine reachable right now? Free calls only (model list / voice list), never a
    loan read, so no quota is spent. Run in parallel; cached for PING_CACHE_S seconds.
    -> {"groq": {"up": True, "seconds": 0.4}, "gemini": {...}, "edge-tts": {...}}"""
    now = time.monotonic()
    if not force and _ping_cache["result"] is not None and now - _ping_cache["at"] < PING_CACHE_S:
        return _ping_cache["result"]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(_PINGS)) as pool:
        result = dict(zip(_PINGS, pool.map(_one_ping, _PINGS)))
    _ping_cache.update(at=now, result=result)
    log.info("ping: %s", {k: ("up" if v["up"] else f"down ({v.get('why')})") for k, v in result.items()})
    return result
