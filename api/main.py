"""KarzSamjho API. Every route in the CLAUDE.md contract exists here.

Checks are REAL (task A7): photo or text -> extract -> maths -> verdict -> Hindi voice.
Results live in memory until the database (A3) arrives, so they are lost on restart.
Cases, events, PDF and verify still return sample data (tasks F1 to F5).

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
import copy
import itertools
import logging
import re
import statistics
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.core import config, extract, maths, speak, verdict
from api.core.config import ensure_dirs
from api.core.schemas import (Case, CaseIn, CheckResult, Event, EventIn, Stats,
                              VerifyResult)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
for noisy in ("httpx", "httpx2", "google_genai.models"):
    logging.getLogger(noisy).setLevel(logging.WARNING)   # httpx logs URLs
log = logging.getLogger("api")

app = FastAPI(title="KarzSamjho API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
ensure_dirs()

# ---------------------------------------------------------------- checks (real, in memory)
CHECKS: dict[str, dict] = {}          # check id -> CheckResult dict, newest last
_ids = itertools.count(1)
SAFE_ID = re.compile(r"^chk_\d{4,}$")

NEXT_STEP = {"code": "ASK_BANK_MITRA", "text_hi": "Loan lene se pehle bank mitra se poochho."}  # D26
NUMBER_ORDER = ("in_hand", "repay_total", "tenure_days", "extra", "per_day", "apr_simple")


def _no_card(code: str, text_hi: str) -> HTTPException:
    """The agreed 'no card' answer (D26): 422 with a Hindi message the user sees as it is."""
    return HTTPException(422, {"code": code, "text_hi": text_hi})


async def run_check(image: bytes | None = None, text: str | None = None) -> dict:
    """One check, start to finish. The AI only reads; every number below is plain Python."""
    start = time.perf_counter()
    try:
        if image is not None:
            read = await run_in_threadpool(extract.extract_from_image, image)
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

    check_id = f"chk_{next(_ids):04d}"
    sentence = speak.speech_text(numbers)
    audio_url = await speak.make_audio(check_id, sentence)
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
        "next_step": dict(NEXT_STEP),
        "speech_text_hi": sentence,
        "audio_url": audio_url,
        "engines": {"read": engines["read"], "second_read": engines["second_read"],
                    "speak": "edge-tts" if audio_url else None},
        "seconds": round(time.perf_counter() - start, 1),
        "cached": False,
    }
    CheckResult.model_validate(result)        # the contract shape, checked before anyone sees it
    CHECKS[check_id] = result
    log.info("check %s: verdict=%s read=%s seconds=%s audio=%s", check_id, result_verdict,
             engines["read"], result["seconds"], bool(audio_url))
    return result


@app.post("/api/checks", response_model=CheckResult)
async def create_check(request: Request):
    """Form field `image` (a photo) or `text`, or JSON {text}; plus lang, source."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(("multipart/form-data", "application/x-www-form-urlencoded")):
        form = await request.form()
        upload = form.get("image")
        if upload is not None and hasattr(upload, "read"):
            image = await upload.read()
            if not image:
                raise _no_card("UNREADABLE", extract.MSG_BAD_PHOTO)
            return await run_check(image=image)
        if form.get("text"):
            return await run_check(text=str(form["text"]))
        raise HTTPException(422, "Send a form field named 'image' or 'text'.")
    if content_type.startswith("application/json"):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("text"):
            raise HTTPException(422, "Send JSON like {\"text\": \"...\"}.")
        return await run_check(text=str(body["text"]))
    raise HTTPException(415, "Send multipart form data (image) or JSON (text).")


@app.get("/api/checks", response_model=list[CheckResult])
def list_checks(limit: int = 20):
    return list(reversed(CHECKS.values()))[:max(limit, 0)]


@app.get("/api/checks/{check_id}", response_model=CheckResult)
def get_check(check_id: str):
    if check_id not in CHECKS:
        raise HTTPException(404, "Check not found.")
    return CHECKS[check_id]


@app.get("/api/audio/{check_id}.mp3")
def get_audio(check_id: str):
    path = Path(config.settings.audio_dir) / f"{check_id}.mp3"
    if not SAFE_ID.match(check_id) or not path.is_file():
        raise HTTPException(404, "No audio for this check.")
    return FileResponse(path, media_type="audio/mpeg", filename=f"{check_id}.mp3")


# ---------------------------------------------------------------- cases (sample data until F1-F5)
SAMPLE_CASE = {
    "id": "case_0007",
    "borrower_name": "Raju (sample)",
    "lender_name": "QuickCash",
    "check_id": "chk_0042",
    "route": "Sachet portal + cybercrime.gov.in / 1930",
    "opened_at": "2026-11-13T12:00:00+05:30",
    "day": 1,
    "events": [
        {"id": "evt_0001", "at": "2026-11-13T21:40:00+05:30", "channel": "call",
         "contacted": "borrower", "text": "Paisa do warna ghar aa jayenge.",
         "rules": ["H1", "H2"], "hash": "a" * 64, "prev_hash": "0" * 64},
        {"id": "evt_0002", "at": "2026-11-14T10:15:00+05:30", "channel": "whatsapp",
         "contacted": "family", "text": "Aapke bhai ne loan nahi chukaya.",
         "rules": ["H3"], "hash": "b" * 64, "prev_hash": "a" * 64},
    ],
}


@app.post("/api/cases", response_model=Case)
def create_case(body: CaseIn):
    case = copy.deepcopy(SAMPLE_CASE)
    case.update(borrower_name=body.borrower_name, lender_name=body.lender_name,
                check_id=body.check_id, events=[])
    return case


@app.get("/api/cases", response_model=list[Case])
def list_cases():
    return [SAMPLE_CASE]


@app.get("/api/cases/{case_id}", response_model=Case)
def get_case(case_id: str):
    if case_id != SAMPLE_CASE["id"]:
        raise HTTPException(404, "Case not found.")
    return SAMPLE_CASE


@app.post("/api/cases/{case_id}/events", response_model=Event)
def add_event(case_id: str, body: EventIn):
    return {"id": "evt_0003", "at": body.at, "channel": body.channel,
            "contacted": body.contacted, "text": body.text, "rules": ["H1"],
            "hash": "c" * 64, "prev_hash": "b" * 64}


@app.get("/api/cases/{case_id}/evidence.pdf")
def evidence_pdf(case_id: str):
    raise HTTPException(404, "No PDF yet (task F3).")


@app.get("/api/cases/{case_id}/verify", response_model=VerifyResult)
def verify_case(case_id: str):
    return {"ok": True}


# ---------------------------------------------------------------- stats, health
@app.get("/api/stats", response_model=Stats)
def stats():
    """From the checks in memory (task A5 moves this to the database)."""
    checks = list(CHECKS.values())
    extra = sum(c["numbers"]["extra"]["value"] or 0 for c in checks
                if c["verdict"] in ("COSTLY", "VERY_COSTLY"))
    return {"checks": len(checks),
            "median_seconds": statistics.median(c["seconds"] for c in checks) if checks else 0,
            "extra_rupees_flagged": extra}


@app.get("/api/health")
def health():
    """Says whether each key is set. Never returns the key values."""
    s = config.settings
    return {
        "api": "up",
        "groq_key": bool(s.groq_api_key),
        "gemini_key": bool(s.gemini_api_key),
        "telegram_key": bool(s.telegram_bot_token),
        "voice": s.voice_enabled,
        "sample_data": False,
        "checks_in_memory": len(CHECKS),
    }
