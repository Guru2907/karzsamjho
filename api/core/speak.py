"""The Hindi sentence Raju hears, and its MP3 (task D2).

The sentence is a fixed template filled by code, never written by an AI
(CLAUDE.md, docs/PLAN.md). The MP3 is made by fallback.speak (edge-tts); this file
never imports edge-tts itself. If the voice fails, make_audio returns None and the
card is sent alone.
"""
import logging
import math
import re
from pathlib import Path

from api.core import config, fallback

log = logging.getLogger("speak")

TEMPLATE = ("Aapko haath mein {in_hand} rupaye milenge. "
            "{days} din mein {repay} rupaye lautane honge. "
            "Yaani {extra} rupaye zyada.")
NOT_CLEAR = ("Is offer ke saare number saaf nahi padhe gaye. "
             "Loan lene se pehle bank mitra se poochho.")
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _spoken(numbers: dict, key: str) -> str | None:
    """A verified number as whole digits with no commas ("3800"), or None."""
    item = numbers.get(key)
    if not isinstance(item, dict) or item.get("status") == "unverified":
        return None
    value = item.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return str(math.floor(value + 0.5))  # whole rupees, halves go up


def speech_text(numbers: dict) -> str:
    """The fixed sentence, or the "not clear" sentence if a needed number is unverified."""
    parts = {name: _spoken(numbers, key) for name, key in (
        ("in_hand", "in_hand"), ("repay", "repay_total"), ("days", "tenure_days"), ("extra", "extra"))}
    if any(v is None for v in parts.values()):
        return NOT_CLEAR
    return TEMPLATE.format(**parts)


async def make_audio(check_id: str, text: str) -> str | None:
    """Write <AUDIO_DIR>/<check_id>.mp3 through fallback.speak.

    -> "/api/audio/<check_id>.mp3", or None if voice is switched off or failed.
    Never raises, so a voice problem can never stop the card.
    """
    s = config.settings
    if not s.voice_enabled or not text or not SAFE_ID.match(check_id or ""):
        return None
    out_path = Path(s.audio_dir) / f"{check_id}.mp3"
    try:
        ok = await fallback.speak(text, str(out_path))
    except Exception as exc:  # e.g. fallback.speak not built yet: no voice, card still goes
        log.warning("voice failed for %s: %s", check_id, type(exc).__name__)
        return None
    if not ok or not out_path.exists() or out_path.stat().st_size == 0:
        return None
    return f"/api/audio/{check_id}.mp3"
