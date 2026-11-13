"""Evidence PDF in ENGLISH (task F3) + masking + hash helpers.

build_pdf(case) -> PDF bytes. case = the GET /api/cases/{id} shape: id, borrower_name,
lender_name, route, opened_at, day, events [{id, at, channel, contacted, text, rules, hash,
prev_hash}]. The PDF has: case details and "Day N of 30", a timeline, the rules broken with
their basis (RBI circular on recovery agents, 12 Aug 2022), every hash, where to complain and
a complaint draft. Any 12-digit number (Aadhaar-like) is masked as "XXXX XXXX 1234".

English only (D20): ReportLab's built-in fonts cannot draw Devanagari or Bengali correctly, so a
message written in those scripts is NOT printed as broken letters; the PDF says the exact words
are kept in the case record and protected by that entry's hash.

event_hash / verify_chain implement CLAUDE.md "hash = SHA-256(prev_hash + event fields)" for F2 /
F4 to use if they want one shared definition.
"""
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from api.core.harass import RULES, RULES_BASIS

IST = timezone(timedelta(hours=5, minutes=30))
GENESIS = "0" * 64
HASH_FIELDS = ("at", "channel", "contacted", "text", "rules")   # exactly as main.py event_hash (F2, #29)
CASE_DAYS = 30

ROUTES = {   # CLAUDE.md "Complaint routes"
    "regulated": ("The lender's grievance officer first. If there is no answer within 30 days: "
                  "RBI Ombudsman, cms.rbi.org.in, phone 14448."),
    "unregulated": ("App not linked to a regulated lender: Sachet portal (sachet.rbi.org.in) and "
                    "cybercrime.gov.in, phone 1930."),
    "threats": "Threats or extortion: local police, cyber crime helpline 1930, emergency 112.",
}

_TWELVE_DIGITS = re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?(\d{4})(?!\d)")
_ASCII_PUNCT = str.maketrans({"₹": "Rs ", "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-",
                              "—": "-", "…": "...", "•": "-", " ": " "})
NON_LATIN_NOTE = ("[Written in Hindi / Bengali / Marathi script. The exact words are kept in the "
                  "case record and protected by this entry's hash.]")


# ---------------------------------------------------------------- masking and hashes
def mask(text: str) -> str:
    """Any 12-digit number (spaces or dashes allowed between groups of 4) -> "XXXX XXXX 1234"."""
    return _TWELVE_DIGITS.sub(lambda m: f"XXXX XXXX {m.group(1)}", text or "")


def event_hash(prev_hash: str, event: dict) -> str:
    """SHA-256(prev_hash + the event's fields as sorted JSON). Editing any field, or the order,
    changes this hash and every hash after it."""
    fields = {k: event.get(k) for k in HASH_FIELDS}
    return hashlib.sha256((prev_hash + json.dumps(fields, sort_keys=True, ensure_ascii=False,
                                                  separators=(",", ":"))).encode("utf-8")).hexdigest()


def verify_chain(events: list[dict]) -> bool:
    """True if every event's prev_hash is the hash before it and its hash matches its fields."""
    prev = GENESIS
    for ev in events:
        if ev.get("prev_hash") != prev or ev.get("hash") != event_hash(prev, ev):
            return False
        prev = ev["hash"]
    return True


# ---------------------------------------------------------------- text helpers
def pdf_text(text: str | None) -> str:
    """Masked, plain text the built-in PDF fonts can draw."""
    text = mask(text or "").translate(_ASCII_PUNCT)
    if any(ord(ch) > 0xFF for ch in text):
        return NON_LATIN_NOTE
    return " ".join(text.split())


def _when(at: str | None) -> str:
    """ISO time -> "13 Nov 2026, 10:40 PM IST" (as written if it cannot be read)."""
    try:
        t = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return pdf_text(str(at or "unknown time"))
    t = t.replace(tzinfo=IST) if t.tzinfo is None else t.astimezone(IST)
    return _clock(t)


def _clock(t: datetime) -> str:
    """"13 Nov 2026, 9:40 PM IST": no leading zeros, the same on every platform."""
    return f"{t.day} {t:%b %Y}, {int(t.strftime('%I'))}:{t:%M %p} IST"


def case_day(case: dict, today: datetime | None = None) -> int | None:
    """The case's "Day N of 30": the API's `day` if given, else counted from opened_at (day 1 = opening day)."""
    if isinstance(case.get("day"), int):
        return case["day"]
    try:
        opened = datetime.fromisoformat(str(case.get("opened_at")).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    opened = opened.replace(tzinfo=IST) if opened.tzinfo is None else opened.astimezone(IST)
    today = (today or datetime.now(IST)).astimezone(IST)
    return max((today.date() - opened.date()).days + 1, 1)


def rule_counts(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ev in events:
        for rule in ev.get("rules") or []:
            if rule in RULES:
                counts[rule] = counts.get(rule, 0) + 1
    return dict(sorted(counts.items()))


def where_to_complain(case: dict, counts: dict[str, int]) -> list[str]:
    """The case's route (from F5) if set; else every route that may apply. Threats add the police line."""
    lines = [pdf_text(case["route"])] if case.get("route") else [ROUTES["regulated"], ROUTES["unregulated"]]
    if ("H2" in counts or "H5" in counts) and ROUTES["threats"] not in lines:
        lines.append(ROUTES["threats"])
    return lines


def complaint_draft(case: dict, counts: dict[str, int]) -> list[str]:
    """A ready complaint letter in English, as paragraphs."""
    events = case.get("events") or []
    lender = pdf_text(case.get("lender_name")) or "the lender"
    borrower = pdf_text(case.get("borrower_name")) or "the borrower"
    span = (f"between {_when(events[0].get('at'))} and {_when(events[-1].get('at'))}"
            if events else "recently")
    broken = "; ".join(f"{r} {RULES[r].lower()} ({n} time{'s' if n != 1 else ''})"
                       for r, n in counts.items()) or "repeated recovery contact"
    return [
        "To: the Grievance Redressal Officer / the authority named above",
        f"Subject: Complaint about harassment by recovery agents of {lender}",
        f"I, {borrower}, have a loan with {lender}. {span[0].upper() + span[1:]}, its recovery "
        f"agents contacted me {len(events)} time{'s' if len(events) != 1 else ''} in ways that go "
        f"against the {RULES_BASIS}: {broken}.",
        "The attached timeline lists each contact with its date, time, channel, who was contacted "
        "and the words used. Each entry is protected by a SHA-256 hash chain, so any later change "
        "to the record can be detected.",
        "I request you to stop this harassment, act against the agents responsible, and reply to "
        "me in writing within 30 days.",
        "Name: ____________________    Date: ____________    Signature: ____________________",
    ]


# ---------------------------------------------------------------- the PDF
def build_pdf(case: dict, compress: bool = True) -> bytes:
    """The case as an English evidence PDF. compress=False only so tests can read the text."""
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=12.5)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10)
    mono = ParagraphStyle("mono", parent=small, fontName="Courier", fontSize=6.5, leading=8)
    h1, h2 = styles["Title"], ParagraphStyle("h2", parent=styles["Heading2"], spaceBefore=10)

    def p(text, style=body):
        return Paragraph(escape(text), style)

    events = case.get("events") or []
    counts = rule_counts(events)
    day = case_day(case)
    out = [
        p("KarzSamjho: harassment evidence", h1),
        p(f"Case {pdf_text(case.get('id'))}  |  Borrower: {pdf_text(case.get('borrower_name'))}  |  "
          f"Lender / app: {pdf_text(case.get('lender_name'))}"),
        p(f"Opened: {_when(case.get('opened_at'))}  |  "
          + (f"Day {day} of {CASE_DAYS}" if day else f"Day count not available (of {CASE_DAYS})")
          + f"  |  Generated: {_clock(datetime.now(IST))}", small),
        p("Synthetic demo data. Any 12-digit number is masked as XXXX XXXX 1234.", small),
    ]

    out.append(p("Rules broken", h2))
    if counts:
        out.append(p(f"Basis: {RULES_BASIS}. H6 is our own threshold, not an RBI number.", small))
        rows = [[p("Rule", small), p("What it means", small), p("Times", small)]]
        rows += [[p(r, small), p(RULES[r], small), p(str(n), small)] for r, n in counts.items()]
        out.append(_table(rows, [18 * mm, 130 * mm, 18 * mm]))
    else:
        out.append(p("No rule was broken in the logged contacts.", body))

    out.append(p(f"Timeline ({len(events)} contact{'s' if len(events) != 1 else ''})", h2))
    if events:
        rows = [[p(h, small) for h in ("#", "When", "Channel / who", "Words used (masked)", "Rules")]]
        for i, ev in enumerate(events, 1):
            rows.append([p(str(i), small), p(_when(ev.get("at")), small),
                         p(f"{pdf_text(ev.get('channel')) or '-'} / {pdf_text(ev.get('contacted')) or '-'}", small),
                         p(pdf_text(ev.get("text")) or "(no words logged)", small),
                         p(", ".join(ev.get("rules") or []) or "none", small)])
        out.append(_table(rows, [8 * mm, 34 * mm, 28 * mm, 82 * mm, 18 * mm]))
    else:
        out.append(p("No contacts logged yet.", body))

    out.append(p("Record integrity (hash chain)", h2))
    out.append(p("Each entry's hash = SHA-256(previous entry's hash + this entry). Changing any entry "
                 "breaks every hash after it; the server's /api/cases/<id>/verify checks the chain.", small))
    for i, ev in enumerate(events, 1):
        out.append(KeepTogether([p(f"#{i}  hash      {pdf_text(ev.get('hash'))}", mono),
                                 p(f"#{i}  prev_hash {pdf_text(ev.get('prev_hash'))}", mono)]))

    out.append(p("Where to complain", h2))
    out += [p(f"- {line}", body) for line in where_to_complain(case, counts)]

    # The letter stays in one piece (on its own page if needed), so it can be printed and signed.
    out.append(KeepTogether([p("Complaint draft", h2)]
                            + [p(line, body) for line in complaint_draft(case, counts)]))

    buf = io.BytesIO()
    old = rl_config.pageCompression
    rl_config.pageCompression = 1 if compress else 0
    try:
        SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=15 * mm, bottomMargin=15 * mm, title="KarzSamjho evidence",
                          author="KarzSamjho").build(out)
    finally:
        rl_config.pageCompression = old
    return buf.getvalue()


def _table(rows, widths):
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa7b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table
