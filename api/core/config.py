"""Settings for the whole app. Read from .env; defaults match CLAUDE.md.

Rules: model names, timeouts and thresholds live here, never hard-coded elsewhere.
Never print or log the key values.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def _s(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _f(name: str, default: float) -> float:
    try:
        return float(_s(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # Keys (never print these)
    telegram_bot_token: str = field(default_factory=lambda: _s("TELEGRAM_BOT_TOKEN"), repr=False)
    gemini_api_key: str = field(default_factory=lambda: _s("GEMINI_API_KEY"), repr=False)
    groq_api_key: str = field(default_factory=lambda: _s("GROQ_API_KEY"), repr=False)

    # Models
    groq_vision_model: str = field(default_factory=lambda: _s("GROQ_VISION_MODEL", "qwen/qwen3.8-27b"))
    gemini_model: str = field(default_factory=lambda: _s("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    groq_text_model: str = field(default_factory=lambda: _s("GROQ_TEXT_MODEL", "openai/gpt-oss-20b"))
    groq_stt_model: str = field(default_factory=lambda: _s("GROQ_STT_MODEL", "whisper-large-v3-turbo"))
    tts_voice_hi: str = field(default_factory=lambda: _s("TTS_VOICE_HI", "hi-IN-SwaraNeural"))

    # Timeouts, in seconds
    vision_timeout_s: float = field(default_factory=lambda: _f("VISION_TIMEOUT_S", 6))
    read_timeout_s: float = field(default_factory=lambda: _f("READ_TIMEOUT_S", 12))
    text_timeout_s: float = field(default_factory=lambda: _f("TEXT_TIMEOUT_S", 5))
    tts_timeout_s: float = field(default_factory=lambda: _f("TTS_TIMEOUT_S", 6))
    stt_timeout_s: float = field(default_factory=lambda: _f("STT_TIMEOUT_S", 8))

    # Storage
    db_path: str = field(default_factory=lambda: _s("DB_PATH", "./karzsamjho.db"))
    cache_dir: str = field(default_factory=lambda: _s("CACHE_DIR", "./cache"))
    audio_dir: str = field(default_factory=lambda: _s("AUDIO_DIR", "./audio"))
    voice_enabled: bool = field(default_factory=lambda: _s("VOICE_ENABLED", "true").lower() == "true")
    api_url: str = field(default_factory=lambda: _s("API_URL", "http://localhost:8000"))

    # Our own thresholds (NOT RBI limits). See CLAUDE.md "The Decide rules".
    band_costly_apr: float = 36.0        # apr_simple >= this -> COSTLY
    band_very_costly_apr: float = 100.0  # apr_simple > this -> VERY_COSTLY
    short_loan_days: int = 30            # upfront fee on a loan this short -> VERY_COSTLY
    crosscheck_tolerance_rs: float = 1.0
    lender_found_score: int = 90
    lender_similar_score: int = 70
    h1_earliest_hour: int = 8            # contact before 08:00 breaks H1
    h1_latest_hour: int = 19             # contact after 19:00 breaks H1
    h6_calls_per_day: int = 5            # our threshold; label it as ours


settings = Settings()


def ensure_dirs() -> None:
    """Create the cache and audio folders if they are missing."""
    Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.audio_dir).mkdir(parents=True, exist_ok=True)
