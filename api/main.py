"""KarzSamjho API. Every route in the CLAUDE.md contract exists here.

Checks are REAL (task A7): photo or text -> extract -> maths -> verdict -> Hindi voice.
Results live in memory until the database (A3) arrives, so they are lost on restart.
Cases, events, PDF and verify still return sample data (tasks F1 to F5).

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
import hashlib
import itertools
import json
import threading
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import re
import statistics
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from api.core import cache, config, db, evidence, extract, fallback, harass, maths, speak, verdict
from api.core.config import ensure_dirs
from api.core.schemas import (Case, CaseIn, CheckResult, Event, EventIn, Stats,
                              VerifyResult)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
for noisy in ("httpx", "httpx2", "google_genai.models"):
    logging.getLogger(noisy).setLevel(logging.WARNING)   # httpx logs URLs
log = logging.getLogger("api")

@asynccontextmanager
async def _lifespan(_app):
    """Create the SQLite tables when the server starts (A3; db.py also does it on first use)."""
    db.init_db()
    log.info("database ready: %s", config.settings.db_path)
    yield


app = FastAPI(title="KarzSamjho API", version="0.3.0", lifespan=_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
ensure_dirs()


# ---------------------------------------------------------------- checks (real, stored in SQLite, A3)
# The database (db.py) is the source of truth. CHECKS is only a fast in-memory copy of this
# run's results; a restart empties it and every read falls back to the database.
CHECKS: dict[str, dict] = {}          # check id -> CheckResult dict
SAFE_ID = re.compile(r"^chk_\d{4,}$")


def _first_free_id() -> int:
    """Continue after the highest check id on disk (database, cached results and MP3s), so a
    new check after a restart never reuses an id or overwrites the MP3 of an old one."""
    numbers = [int(r["id"][4:]) for r in cache.all_results()
               if isinstance(r.get("id"), str) and SAFE_ID.match(r["id"])]
    numbers.append(db.max_check_number())
    audio = Path(config.settings.audio_dir)
    if audio.is_dir():
        numbers += [int(p.stem[4:]) for p in audio.glob("chk_*.mp3") if SAFE_ID.match(p.stem)]
    return max(numbers, default=0) + 1


_ids = None                           # started on first use, so loading this file never opens the database


def _new_check_id() -> str:
    global _ids
    if _ids is None:
        _ids = itertools.count(_first_free_id())
    return f"chk_{next(_ids):04d}"


async def _from_cache(key: str, start: float, lang: str = "hi") -> dict | None:
    """A repeated photo: the stored result, no AI call. Makes the MP3 again only if it is gone
    (edge-tts is not an AI reader), in the same language (D7: never a Hindi MP3 for bn / mr)."""
    hit = cache.get(key)
    if hit is None:
        return None
    try:
        result = CheckResult.model_validate(hit).model_dump()
    except ValueError:
        return None                                   # an old or broken entry is a miss
    mp3 = Path(config.settings.audio_dir) / f"{result['id']}.mp3"
    if config.settings.voice_enabled and (not result["audio_url"] or not mp3.is_file()):
        result["audio_url"] = await speak.make_audio(result["id"], result["speech_text_hi"], lang)
        result["engines"]["speak"] = "edge-tts" if result["audio_url"] else None
        cache.put(key, result)
    result.update(cached=True, seconds=round(time.perf_counter() - start, 1))
    CHECKS[result["id"]] = result
    db.save_check(result, key, "cache", replace=False)    # keeps the first stored answer
    log.info("check %s: cache hit, no AI call, seconds=%s", result["id"], result["seconds"])
    return result

NEXT_STEP = {"code": "ASK_BANK_MITRA", "text_hi": "Loan lene se pehle bank mitra se poochho."}  # D26
# B9: the offer asks for money BEFORE the loan (advance-fee fraud). Fixed text, filled by code.
PAY_FIRST_STEP = {"code": "DO_NOT_PAY_FIRST",
                  "text_hi": "Paise mat bhejo. Loan se pehle paise maangna dhokha ho sakta hai. "
                             "Shikayat: 1930 ya cybercrime.gov.in"}
PAY_FIRST_WARNING = ("Savdhaan! Yeh offer loan dene se pehle aapse {amount} rupaye maang raha hai. "
                     "Loan se pehle paise maangna dhokha ho sakta hai. Paise mat bhejo.")
# The same warning in the voice's own language and script (bn / mr voices cannot read Hinglish).
# Drafts: a native speaker approves them like the D7 sentences (D32).
PAY_FIRST_WARNINGS = {
    "hi": PAY_FIRST_WARNING,
    "bn": ("সাবধান! এই অফার লোন দেওয়ার আগেই আপনার কাছ থেকে {amount} টাকা চাইছে। "
           "লোনের আগে টাকা চাওয়া প্রতারণা হতে পারে। টাকা পাঠাবেন না।"),
    "mr": ("सावधान! ही ऑफर कर्ज देण्याआधीच तुमच्याकडून {amount} रुपये मागत आहे. "
           "कर्जाआधी पैसे मागणे फसवणूक असू शकते. पैसे पाठवू नका."),
}
NUMBER_ORDER = ("in_hand", "repay_total", "tenure_days", "extra", "per_day", "apr_simple")


def _lang(value) -> str:
    """The voice language asked for: "hi", "bn" or "mr" (D7, D33). Anything else -> "hi"."""
    lang = str(value or "hi").strip().lower()
    return lang if lang in config.LANGS else "hi"


def _no_card(code: str, text_hi: str) -> HTTPException:
    """The agreed 'no card' answer (D26): 422 with a Hindi message the user sees as it is."""
    return HTTPException(422, {"code": code, "text_hi": text_hi})


async def run_check(image: bytes | None = None, text: str | None = None,
                    audio: bytes | None = None, lang: str = "hi", source: str = "api") -> dict:
    """One check, start to finish. The AI only reads; every number below is plain Python.
    A voice note (audio, D6) is read like a pasted SMS: no cache, no second reading."""
    start = time.perf_counter()
    key = cache.image_key(image, lang) if image is not None else None
    if key:
        hit = await _from_cache(key, start, lang)
        if hit:
            return hit
    try:
        if image is not None:
            read = await run_in_threadpool(extract.extract_from_image, image)
        elif audio is not None:
            read = await run_in_threadpool(extract.extract_from_voice, audio)
        else:
            read = await run_in_threadpool(extract.extract_from_text, text)
    except extract.NotALoan as exc:
        raise _no_card("NOT_A_LOAN", exc.text_hi)
    except extract.Unreadable as exc:
        raise _no_card("UNREADABLE", exc.text_hi)

    disputed: list[str] = []
    problems = maths.cross_check(read["fields"])
    if problems and image is not None:
        # The sums do not add up: the OTHER reader reads the photo again (B6). Fields the two
        # disagree on are disputed. For text there is no second reader; fill_gaps then
        # treats every sum that does not add up as unverified.
        log.info("cross-check: sums do not add up for %s; second reading", problems)
        read, disputed = await run_in_threadpool(extract.second_reading, image, read, problems)
        log.info("second reading by %s: disputed %s", read["engines"]["second_read"], disputed)
    engines = read["engines"]
    # Disputed values are set aside before any maths. A sum that still fails after that
    # means the ad contradicts itself (fill_gaps then marks those numbers unverified too).
    fields = {k: None if k in disputed else v for k, v in read["fields"].items()}
    still_wrong = maths.cross_check(fields)

    numbers = maths.compute(maths.fill_gaps(fields, disputed))
    numbers = {k: numbers[k] for k in NUMBER_ORDER}
    fees = None if "fees" in disputed or "fees" in still_wrong else fields["fees"]
    result_verdict = verdict.decide(numbers, fees)

    check_id = _new_check_id()
    sentence = speak.speech_text(numbers, lang)          # bn / mr: that language's sentence (D7)
    pay_first = fields.get("pay_first")
    if pay_first:                                    # B9: the warning comes first, then the numbers
        warning = PAY_FIRST_WARNINGS.get(lang, PAY_FIRST_WARNING)    # same language as the voice
        sentence = warning.format(amount=int(round(pay_first))) + " " + sentence
    audio_url = await speak.make_audio(check_id, sentence, lang)
    # Names shown as "couldn't verify": every unverified number, plus any raw field that was
    # disputed or contradicts itself, unless the card still has a verified number of that name.
    unverified = sorted({k for k, v in numbers.items() if v["status"] == "unverified"}
                        | {k for k in set(disputed) | set(still_wrong)
                           if k not in numbers or numbers[k]["status"] == "unverified"})

    result = {
        "id": check_id,
        "verdict": result_verdict,
        "numbers": numbers,
        "unverified": unverified,
        "lender": {"name_read": fields["app_name"] or fields["lender_name"], "match": None,
                   "score": None, "closest": None, "list_date": None},
        "next_step": dict(PAY_FIRST_STEP if pay_first else NEXT_STEP),
        "speech_text_hi": sentence,
        "audio_url": audio_url,
        "engines": {"read": engines["read"], "second_read": engines["second_read"],
                    "speak": "edge-tts" if audio_url else None,
                    "listen": engines.get("listen")},
        "seconds": round(time.perf_counter() - start, 1),
        "cached": False,
    }
    CheckResult.model_validate(result)        # the contract shape, checked before anyone sees it
    CHECKS[check_id] = result
    db.save_check(result, key, source)        # A3: survives a restart
    if key:
        try:
            cache.put(key, result)            # photos only (A4); a failed write never stops the answer
        except OSError as exc:
            log.warning("cache write failed for %s: %s", check_id, type(exc).__name__)
    log.info("check %s: verdict=%s read=%s seconds=%s audio=%s", check_id, result_verdict,
             engines["read"], result["seconds"], bool(audio_url))
    return result


@app.post("/api/checks", response_model=CheckResult)
async def create_check(request: Request):
    """Form field `image` (a photo), `audio` (a voice note) or `text`, or JSON {text}; plus lang, source."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(("multipart/form-data", "application/x-www-form-urlencoded")):
        form = await request.form()
        lang = _lang(form.get("lang"))
        source = str(form.get("source") or "api")[:20]
        upload = form.get("image")
        if upload is not None and hasattr(upload, "read"):
            image = await upload.read()
            if not image:
                raise _no_card("UNREADABLE", extract.MSG_BAD_PHOTO)
            return await run_check(image=image, lang=lang, source=source)
        voice = form.get("audio")                     # a Telegram voice note, OGG (D6, D33)
        if voice is not None and hasattr(voice, "read"):
            audio = await voice.read()
            if not audio:
                raise _no_card("UNREADABLE", extract.MSG_BAD_VOICE)
            return await run_check(audio=audio, lang=lang, source=source)
        if form.get("text"):
            return await run_check(text=str(form["text"]), lang=lang, source=source)
        raise HTTPException(422, "Send a form field named 'image', 'audio' or 'text'.")
    if content_type.startswith("application/json"):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("text"):
            raise HTTPException(422, "Send JSON like {\"text\": \"...\"}.")
        return await run_check(text=str(body["text"]), lang=_lang(body.get("lang")),
                               source=str(body.get("source") or "api")[:20])
    raise HTTPException(415, "Send multipart form data (image) or JSON (text).")


@app.get("/api/checks", response_model=list[CheckResult])
def list_checks(limit: int = 20):
    return db.list_checks(limit)


@app.get("/api/checks/{check_id}", response_model=CheckResult)
def get_check(check_id: str):
    result = CHECKS.get(check_id) or db.get_check(check_id)
    if result is None:
        raise HTTPException(404, "Check not found.")
    return result


@app.get("/api/audio/{check_id}.mp3")
def get_audio(check_id: str):
    path = Path(config.settings.audio_dir) / f"{check_id}.mp3"
    if not SAFE_ID.match(check_id) or not path.is_file():
        raise HTTPException(404, "No audio for this check.")
    return FileResponse(path, media_type="audio/mpeg", filename=f"{check_id}.mp3")


# ---------------------------------------------------------------- cases and events (real, F2)
_chain_lock = threading.Lock()        # one event at a time per process, so the chain never forks


def event_hash(prev_hash: str, event: dict) -> str:
    """hash = SHA-256(prev_hash + the event's fields), fields as compact sorted JSON (CLAUDE.md, F2).
    F4 (verify) recomputes exactly this, so any later edit to a stored event breaks the chain."""
    fields = {k: event.get(k) for k in ("at", "channel", "contacted", "text", "rules")}
    body = json.dumps(fields, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256((prev_hash + body).encode("utf-8")).hexdigest()


def _ist(at: str) -> datetime:
    """An ISO time; a time without a zone is taken as IST."""
    when = datetime.fromisoformat(at.replace("Z", "+00:00"))
    return when if when.tzinfo else when.replace(tzinfo=db.IST)


def _with_day(case: dict) -> dict:
    """Adds the day counter: day 1 is the day the case was opened (IST)."""
    opened = _ist(case["opened_at"]).astimezone(db.IST).date()
    today = datetime.now(db.IST).date()
    return {**case, "day": (today - opened).days + 1}


def _rules(event: dict, calls_that_day: int) -> list[str]:
    """Siddeshwar's harass.label (F1). Until it is merged, or if it fails, the event is still stored
    (with no rules) so the record and its chain are never lost."""
    label = getattr(harass, "label", None)
    if label is None:
        log.warning("harass.label not available yet (F1): event stored without rules")
        return []
    try:
        return sorted(set(label(event, calls_that_day)))
    except NotImplementedError:
        log.warning("harass.label not built yet (F1): event stored without rules")
        return []
    except Exception as exc:                                  # never lose the evidence itself
        log.warning("harass.label failed (%s): event stored without rules", type(exc).__name__)
        return []


@app.post("/api/cases", response_model=Case)
def create_case(body: CaseIn):
    return _with_day(db.create_case(body.borrower_name, body.lender_name, body.check_id))


@app.get("/api/cases", response_model=list[Case])
def list_cases():
    return [_with_day(c) for c in db.list_cases()]


@app.get("/api/cases/{case_id}", response_model=Case)
def get_case(case_id: str):
    case = db.get_case(case_id)
    if case is None:
        raise HTTPException(404, "Case not found.")
    return _with_day(case)


@app.post("/api/cases/{case_id}/events", response_model=Event)
def add_event(case_id: str, body: EventIn):
    """Log one threat / message / call: rules H1-H6 (F1), then hash-chained storage (F2)."""
    if db.get_case(case_id) is None:
        raise HTTPException(404, "Case not found.")
    try:
        when = _ist(body.at)
    except ValueError:
        raise HTTPException(422, {"code": "BAD_TIME", "text_hi": "Samay sahi nahi hai. Dobara bhejo."})
    event = {"at": when.isoformat(timespec="seconds"), "channel": body.channel.strip().lower(),
             "contacted": body.contacted.strip().lower(), "text": body.text}
    with _chain_lock:
        # calls on that date INCLUDING this one (H6 counts the call being logged now)
        calls = db.calls_on(case_id, event["at"][:10]) + (1 if event["channel"] == "call" else 0)
        event["rules"] = _rules(event, calls)
        prev = db.last_event_hash(case_id)
        stored = db.add_event(case_id, {**event, "prev_hash": prev, "hash": event_hash(prev, event)})
    log.info("case %s: event %s rules=%s", case_id, stored["id"], stored["rules"])
    return stored


@app.get("/api/cases/{case_id}/evidence.pdf")
def evidence_pdf(case_id: str):
    """The case as Siddeshwar's English evidence PDF (F3): timeline, rules, hashes, masked numbers,
    complaint draft. Built fresh from the database on every request, so it always has every event."""
    case = db.get_case(case_id)
    if case is None:
        raise HTTPException(404, "Case not found.")
    pdf = evidence.build_pdf(_with_day(case))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{case_id}_evidence.pdf"'})


@app.get("/api/cases/{case_id}/verify", response_model=VerifyResult)
def verify_case(case_id: str):
    return {"ok": True}


# ---------------------------------------------------------------- stats, health
@app.get("/api/stats", response_model=Stats)
def stats():
    """From every stored check (A3), not just since the last restart."""
    checks = db.check_summaries()
    extra = sum(c["extra"] or 0 for c in checks if c["verdict"] in ("COSTLY", "VERY_COSTLY"))
    seconds = [c["seconds"] for c in checks if c["seconds"] is not None]
    return {"checks": len(checks),
            "median_seconds": statistics.median(seconds) if seconds else 0,
            "extra_rupees_flagged": extra}


@app.get("/api/health")
def health(fresh: bool = False):
    """Is each part working right now (A5)? Keys are shown only as set / not set, never their values.
    engines: a free live ping of Groq, Gemini and edge-tts (cached 60 s; ?fresh=true to re-check)."""
    s = config.settings
    try:
        stored, database = len(db.check_summaries()), "up"
    except Exception as exc:                                  # the API still answers if the file is broken
        stored, database = None, f"down ({type(exc).__name__})"
    engines = fallback.ping(force=fresh)
    return {
        "api": "up",
        "groq_key": bool(s.groq_api_key),
        "gemini_key": bool(s.gemini_api_key),
        "telegram_key": bool(s.telegram_bot_token),
        "voice": s.voice_enabled,
        "sample_data": False,
        "database": database,
        "checks_stored": stored,
        "engines": engines,
        "can_read_photos": engines["groq"]["up"] or engines["gemini"]["up"],
        "can_speak": s.voice_enabled and engines["edge-tts"]["up"],
    }
