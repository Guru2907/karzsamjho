"""Harassment rules H1-H6 (task F1). Basis: RBI circular on recovery agents, 12 Aug 2022.

label(event, calls_that_day) -> sorted rule ids, e.g. ["H1", "H2"]; [] for a polite reminder.

H1 (time), H6 (call count) and H3 when `contacted` is family / employer / contacts are plain
code. H2 to H5 in the text come from the text model (fallback.read_text, temperature 0 JSON,
checked by a parser) PLUS a Hinglish + English (+ Devanagari) keyword list. The keywords are the
whole answer when the model is down or answers badly, and a safety net when it answers: in the
13 Nov real run the model missed "family ko sab bata diya" (H3) and "warna police aayegi" (H2),
and a missed rule is the worst failure for evidence. The AI only labels; it never decides the
time or the count.
"""
import json
import logging
import re
from datetime import datetime, timedelta, timezone

from api.core import config, fallback

log = logging.getLogger("harass")

IST = timezone(timedelta(hours=5, minutes=30))
TEXT_RULES = ("H2", "H3", "H4", "H5")

# What each rule means, in English (used on the evidence PDF too).
RULES = {
    "H1": "Contact before 08:00 or after 19:00",
    "H2": "Threats or abusive language",
    "H3": "Contacting family, friends, employer or phone contacts",
    "H4": "Public shaming (sharing photos, posting, telling neighbours)",
    "H5": "False claims of arrest, court order or police action",
    "H6": "5 or more calls in one day (our threshold, not an RBI number)",
}
RULES_BASIS = "RBI circular on recovery agents, 12 Aug 2022"

THIRD_PARTIES = {"family", "employer", "contacts", "friends"}   # `contacted` values that break H3

PROMPT = """You check one message or call note from a loan recovery agent in India.
Answer ONLY one JSON object, no other text:
{"H2": true or false, "H3": true or false, "H4": true or false, "H5": true or false}
H2: threats (of harm, of coming home, of police or other consequences, "warna ...", "nahi to ...") or abusive / insulting words.
H3: says they contacted, told, or will contact the borrower's family, relatives, friends, employer or phone contacts
    (e.g. "aapke bhai ko bata diya", "family ko sab bata diya", "your office will know").
H4: public shaming: sharing or posting the borrower's photo, calling him a fraud/defaulter in front of others
    (e.g. "your family will know you are a defaulter"), telling neighbours or groups.
H5: claims of arrest, police, FIR, jail, court case, warrant or legal action as a threat.
More than one can be true.
A polite payment reminder is all false. Judge only what the text says.

MESSAGE:
"""

# Keyword backup. Word-start matches only, so "maar" does not hit "maarket".
KEYWORDS = {
    "H2": ["warna", "nahi to", "nahin to", "nahi kiya to", "nahi kiye to", "nahi diya to",
           "nahi chukaya to", "nahi bhara to", "dekh lenge", "dekh lunga", "maar", "jaan se", "uthwa",
           "utha lenge", "ghar aa jayenge", "ghar aayenge", "ghar pe aa", "bhugtoge", "bhugatna",
           "anjaam", "kutte", "kamine", "kamina", "saale", "saala", "harami", "dhamki", "chhodenge nahi",
           "threat", "kill", "beat you", "we will come", "come to your house", "consequences",
           "you will regret", "bastard", "idiot",
           "वरना", "नहीं तो", "देख लेंगे", "मार", "जान से", "घर आ जाएंगे", "अंजाम", "कमीने", "साले"],
    "H3": ["aapke bhai", "tumhare bhai", "family ko", "parivaar", "parivar", "ghar walon", "gharwalon",
           "ghar waalon", "rishtedar", "rishtedaron", "contacts ko", "contact list", "dosto ko", "doston ko",
           "office mein", "office me ", "boss ko", "employer", "colleague", "your family", "your relatives",
           "your contacts", "your friends", "your office", "your boss",
           "परिवार", "घर वालों", "घरवालों", "रिश्तेदार", "दोस्तों को", "ऑफिस"],
    "H4": ["viral", "social media", "facebook", "instagram", "whatsapp group", "group mein", "post kar",
           "sabko bata", "sab ko bata", "mohalle", "mohalla", "padosi", "padosiyon", "neighbour", "neighbor",
           "poster", "defaulter", "morph", "share your photo", "photo share", "fraud hai", "chor hai",
           "वायरल", "पड़ोसी", "मोहल्ले", "फोटो"],
    # Not plain "fir": in Hinglish it usually means "phir" (then). "thane" is also a city.
    "H5": ["police", "arrest", "giraftar", "griftar", "jail", "court", "warrant", "case darj",
           "fir darj", "fir file", "fir lodge", "fir karwa", "fir kar", "legal action", "cyber cell",
           "thana", "cbi",
           "पुलिस", "गिरफ्तार", "जेल", "कोर्ट", "वारंट", "थाना"],
}
_PATTERNS = {rule: re.compile("|".join(r"(?<!\w)" + re.escape(w) for w in words), re.IGNORECASE)
             for rule, words in KEYWORDS.items()}


def _ist_time(at: str | None) -> datetime | None:
    """The event time in IST, or None if it cannot be read. A time with no zone counts as IST."""
    if not at:
        return None
    try:
        when = datetime.fromisoformat(str(at).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return when.replace(tzinfo=IST) if when.tzinfo is None else when.astimezone(IST)


def breaks_h1(at: str | None) -> bool:
    """Before 08:00 or after 19:00 IST (hours from config). 19:00:00 itself is not after 19:00."""
    when = _ist_time(at)
    if when is None:
        return False
    s = config.settings
    minutes = when.hour * 60 + when.minute + when.second / 60
    return minutes < s.h1_earliest_hour * 60 or minutes > s.h1_latest_hour * 60


def breaks_h6(calls_that_day: int) -> bool:
    """5 or more calls in one day (our threshold, config h6_calls_per_day)."""
    return isinstance(calls_that_day, int) and calls_that_day >= config.settings.h6_calls_per_day


def parse_labels(raw: str) -> set[str]:
    """check= for read_text: the model's JSON -> the text rules it says are broken.
    Raises on anything that is not a JSON object with true/false for H2 to H5."""
    text = re.sub(r"```(?:json|JSON)?", "", raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    data = json.loads(text[start:end + 1] if start != -1 and end > start else text)
    if not isinstance(data, dict) or not all(isinstance(data.get(r), bool) for r in TEXT_RULES):
        raise ValueError("labels must be true/false for H2 to H5")
    return {r for r in TEXT_RULES if data[r]}


def keyword_labels(text: str) -> set[str]:
    """Backup when the text model is down: rules whose words appear in the text."""
    return {rule for rule, pattern in _PATTERNS.items() if pattern.search(text or "")}


def text_labels(text: str) -> tuple[set[str], str]:
    """(H2-H5 rules found in the text, engine: "gpt-oss-20b" | "gpt-oss-20b+keywords" | "keywords" | "none").

    Model answer + keyword hits (safety net). Model down or bad answer -> keywords alone.
    """
    if not text or not text.strip():
        return set(), "none"
    words = keyword_labels(text)
    try:
        raw, engine, _ = fallback.read_text(PROMPT + text, check=parse_labels)
    except fallback.EngineError:
        log.info("harass: text model unavailable, using the keyword backup")
        return words, "keywords"
    ai = parse_labels(raw)
    if words - ai:
        log.info("harass: keywords added %s to the model's %s", sorted(words - ai), sorted(ai))
        return ai | words, f"{engine}+keywords"
    return ai, engine


def label(event: dict, calls_that_day: int) -> list[str]:
    """event = {"at": ISO time (+05:30), "channel", "contacted", "text"};
    calls_that_day = calls to this case on that date INCLUDING this one.
    -> sorted rule ids, e.g. ["H1", "H2"]; [] for the polite 11 AM reminder."""
    rules = set()
    if breaks_h1(event.get("at")):
        rules.add("H1")
    if breaks_h6(calls_that_day):
        rules.add("H6")
    if str(event.get("contacted") or "").strip().lower() in THIRD_PARTIES:
        rules.add("H3")
    found, _ = text_labels(event.get("text") or "")
    return sorted(rules | found)
