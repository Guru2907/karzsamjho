"""Results stored by SHA-256 of the image bytes. A hit returns the stored result and audio and never calls an AI service.

Task A4. One JSON file per photo in CACHE_DIR (kept on disk, so it survives a restart;
cache/ is in .gitignore). The MP3 stays in AUDIO_DIR under the check id.
"""
import hashlib
import json
import logging
import os
import re
from pathlib import Path

from api.core import config

log = logging.getLogger("cache")
_KEY = re.compile(r"^[0-9a-f]{64}$")


def image_key(image_bytes: bytes, lang: str = "hi") -> str:
    """SHA-256 of the exact image bytes, as hex.

    For Hindi it is exactly sha256(image), so every result cached before D7 stays valid.
    For bn / mr the language is part of the key (D35): a Hindi MP3 must never answer a
    Bengali or Marathi request for the same photo.
    """
    if lang == "hi":
        return hashlib.sha256(image_bytes).hexdigest()
    return hashlib.sha256(image_bytes + b"|lang=" + lang.encode()).hexdigest()


def _path(key: str) -> Path:
    if not _KEY.match(key or ""):
        raise ValueError("not a SHA-256 key")
    return Path(config.settings.cache_dir) / f"{key}.json"


def get(key: str) -> dict | None:
    """The stored CheckResult for this photo, or None (missing or unreadable file = a miss)."""
    try:
        path = _path(key)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("cache miss for %s...: %s", key[:12], type(exc).__name__)
        return None


def put(key: str, result: dict) -> None:
    """Store a CheckResult. Written to a .part file and renamed, so a half file is never read."""
    path = _path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    os.replace(part, path)


def all_results() -> list[dict]:
    """Every stored result (used at start-up so check ids never repeat)."""
    folder = Path(config.settings.cache_dir)
    out = []
    for path in folder.glob("*.json") if folder.is_dir() else []:
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return out
