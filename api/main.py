"""KarzSamjho API. Every route in the CLAUDE.md contract exists here.

RIGHT NOW EVERY ROUTE RETURNS SAMPLE DATA (task A2). Real logic replaces the
samples task by task; the routes and response shapes must stay the same.

Run:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""
import copy

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import ensure_dirs, settings
from api.core.schemas import (Case, CaseIn, CheckResult, Event, EventIn, Stats,
                              VerifyResult)

app = FastAPI(title="KarzSamjho API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
ensure_dirs()

# ---------------------------------------------------------------- sample data
SAMPLE_CHECK = {
    "id": "chk_0042",
    "verdict": "VERY_COSTLY",
    "numbers": {
        "in_hand": {"value": 3800, "status": "derived"},
        "repay_total": {"value": 5000, "status": "read"},
        "tenure_days": {"value": 7, "status": "read"},
        "extra": {"value": 1200, "status": "computed"},
        "per_day": {"value": 171, "status": "computed"},
        "apr_simple": {"value": 1647, "status": "computed"},
    },
    "unverified": ["interest_rate"],
    "lender": {"name_read": "QuickCash", "match": "NOT_FOUND", "score": 41,
               "closest": None, "list_date": "2026-11-12"},
    "next_step": {"code": "ASK_BANK_MITRA", "text_hi": "Bank mitra se poochho"},
    "speech_text_hi": ("Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye "
                       "lautane honge. Yaani 1200 rupaye zyada."),
    "audio_url": "/api/audio/chk_0042.mp3",
    "engines": {"read": "sample", "second_read": None, "speak": None},
    "seconds": 5.4,
    "cached": False,
}

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


# ---------------------------------------------------------------- checks
@app.post("/api/checks", response_model=CheckResult)
async def create_check(request: Request):
    """Form field `image` (a photo) or JSON {text}; plus lang, source. Sample answer for now."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        if form.get("image") is None and not form.get("text"):
            raise HTTPException(422, "Send a form field named 'image' or 'text'.")
    elif content_type.startswith("application/json"):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("text"):
            raise HTTPException(422, "Send JSON like {\"text\": \"...\"}.")
    else:
        raise HTTPException(415, "Send multipart form data (image) or JSON (text).")
    return SAMPLE_CHECK


@app.get("/api/checks", response_model=list[CheckResult])
def list_checks(limit: int = 20):
    return [SAMPLE_CHECK][:limit]


@app.get("/api/checks/{check_id}", response_model=CheckResult)
def get_check(check_id: str):
    if check_id != SAMPLE_CHECK["id"]:
        raise HTTPException(404, "Check not found.")
    return SAMPLE_CHECK


@app.get("/api/audio/{check_id}.mp3")
def get_audio(check_id: str):
    raise HTTPException(404, "No audio yet (task D2).")


# ---------------------------------------------------------------- cases
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
    return {"checks": 1, "median_seconds": 5.4, "extra_rupees_flagged": 1200}


@app.get("/api/health")
def health():
    """Says whether each key is set. Never returns the key values."""
    return {
        "api": "up",
        "groq_key": bool(settings.groq_api_key),
        "gemini_key": bool(settings.gemini_api_key),
        "telegram_key": bool(settings.telegram_bot_token),
        "sample_data": True,
    }
