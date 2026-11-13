"""Pydantic models for the API contract in CLAUDE.md.

Do NOT change these shapes without the whole team agreeing.
"""
from typing import Literal, Optional

from pydantic import BaseModel

Status = Literal["read", "derived", "computed", "unverified"]
Verdict = Literal["USUAL", "COSTLY", "VERY_COSTLY", "CANNOT_SAY"]
LenderMatch = Literal["FOUND", "SIMILAR", "NOT_FOUND"]


class NumberField(BaseModel):
    value: Optional[float] = None
    status: Status


class Lender(BaseModel):
    name_read: Optional[str] = None
    match: Optional[LenderMatch] = None   # null = not checked yet (D26); the card hides the line
    score: Optional[float] = None
    closest: Optional[str] = None
    list_date: Optional[str] = None
    # D51 (additive, null by default). Without these two lines FastAPI's response_model dropped them, so the
    # bot never saw the RBI cancelled-registration line or the registered-NBFC line (finding F-1, D52 run).
    nbfc: Optional[dict] = None           # {name, list_date}: an NBFC registered with RBI
    warning: Optional[dict] = None        # {list, name, source_type, date, source}: RBI cancelled registration


class NextStep(BaseModel):
    code: str
    text_hi: str


class Engines(BaseModel):
    read: Optional[str] = None
    second_read: Optional[str] = None
    speak: Optional[str] = None
    listen: Optional[str] = None          # "whisper" for a voice note (D33); additive


class CheckResult(BaseModel):
    id: str
    verdict: Verdict
    numbers: dict[str, NumberField]
    unverified: list[str] = []
    lender: Lender
    next_step: NextStep
    speech_text_hi: str
    audio_url: Optional[str] = None
    engines: Engines
    seconds: float
    cached: bool = False


class TextCheckIn(BaseModel):
    text: str
    lang: str = "hi"
    source: str = "web"


class CaseIn(BaseModel):
    borrower_name: str
    lender_name: str
    check_id: Optional[str] = None


class EventIn(BaseModel):
    at: str                      # ISO date-time, e.g. 2026-11-13T21:40:00+05:30
    channel: str                 # call | sms | whatsapp | telegram | visit
    contacted: str               # borrower | family | employer | contacts
    text: str = ""


class Event(BaseModel):
    id: str
    at: str
    channel: Optional[str] = None
    contacted: Optional[str] = None
    text: Optional[str] = None
    rules: list[str] = []
    hash: str
    prev_hash: str


class Case(BaseModel):
    id: str
    borrower_name: str
    lender_name: str
    check_id: Optional[str] = None
    route: Optional[str] = None
    opened_at: str
    day: Optional[int] = None    # day counter, e.g. day 1 of 30
    events: list[Event] = []


class VerifyResult(BaseModel):
    ok: bool


class Stats(BaseModel):
    checks: int
    median_seconds: float
    extra_rupees_flagged: float
