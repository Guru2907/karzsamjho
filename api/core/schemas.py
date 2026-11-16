"""Pydantic models for the API contract in CLAUDE.md.

Do NOT change these shapes without the whole team agreeing.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["read", "derived", "computed", "unverified"]
Verdict = Literal["USUAL", "COSTLY", "VERY_COSTLY", "CANNOT_SAY"]
LenderMatch = Literal["FOUND", "SIMILAR", "NOT_FOUND"]


class NumberField(BaseModel):
    value: Optional[float] = None
    status: Status


class LenderNbfc(BaseModel):
    """C3 / D51: the lender is an NBFC registered with RBI."""
    name: str
    list_date: Optional[str] = None


class LenderWarning(BaseModel):
    """D51: the name is on RBI's cancelled-registration list (exact name only). A dated fact, never "fraud"."""
    list: str
    name: str
    source_type: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None


class Lender(BaseModel):
    name_read: Optional[str] = None
    match: Optional[LenderMatch] = None   # null = not checked yet (D26); the card hides the line
    score: Optional[float] = None
    closest: Optional[str] = None
    list_date: Optional[str] = None
    # D51, optional and additive: without these two the API's response model dropped them, so the
    # Telegram card and the web card never saw the warning (the voice did: it is built before the response).
    nbfc: Optional[LenderNbfc] = None
    warning: Optional[LenderWarning] = None


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
    borrower_phone: Optional[str] = None     # masked by the API to XXXXXX 1234 before it is stored (D59)
    telegram_chat: Optional[str] = Field(None, pattern=r"^[0-9a-f]{32,64}$")   # the bot's scrambled chat key


class PhoneIn(BaseModel):
    borrower_phone: str                      # masked by the API to XXXXXX 1234 before it is stored


class ChatLangIn(BaseModel):
    lang: str


class ChatState(BaseModel):
    """What the bot remembers about one Telegram chat, kept in the database (D59)."""
    lang: Optional[str] = None
    case_id: Optional[str] = None
    code: Optional[str] = None
    has_phone: bool = False
    closed: bool = False


class EventIn(BaseModel):
    at: str                      # ISO date-time, e.g. 2026-11-13T21:40:00+05:30
    channel: str                 # call | sms | whatsapp | telegram | visit
    contacted: str               # borrower | family | employer | contacts
    text: str = ""
    threat_type: Optional[str] = None   # death | verbal | legal | shaming | visit | other (D60)


class PhotoRef(BaseModel):
    id: str
    sha256: str                  # its fingerprint, part of the event's hash (D60)


class CloseIn(BaseModel):
    reason: str                  # resolved | repaid | complaint_filed | stopped | other
    note: Optional[str] = None


class Event(BaseModel):
    id: str
    at: str
    channel: Optional[str] = None
    contacted: Optional[str] = None
    text: Optional[str] = None
    rules: list[str] = []
    hash: str
    prev_hash: str
    threat_type: Optional[str] = None
    photos: list[PhotoRef] = []


class Case(BaseModel):
    id: str
    code: Optional[str] = None             # 8 digits, made once with the case, never changed (D59)
    borrower_name: str
    borrower_phone: Optional[str] = None   # always masked: XXXXXX 1234
    source: Optional[str] = None           # telegram | app
    lender_name: str
    check_id: Optional[str] = None
    route: Optional[str] = None
    opened_at: str
    closed_at: Optional[str] = None        # D60: closed for good; no new threats after this
    close_reason: Optional[str] = None
    close_note: Optional[str] = None
    day: Optional[int] = None    # day counter, e.g. day 1 of 30 (stops when the case is closed)
    events: list[Event] = []


class VerifyResult(BaseModel):
    ok: bool


class Stats(BaseModel):
    checks: int
    median_seconds: float
    extra_rupees_flagged: float
