"""Photo or text -> fields (through fallback.py). The AI only copies written numbers; it never calculates. Strip ```json fences, validate with Pydantic. Ignore an AI in_hand the ad did not state.

Filled by task(s): B1, B2, B7, B8 (B6 second reading comes in L5). Signatures in docs/PLAN.md.

Every function returns  {"fields": {<the 10 keys>}, "engines": {"read": ..., "second_read": None}}
or raises NotALoan / Unreadable, each carrying the Hindi message (text_hi) the user sees.
"""
import json
import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from api.core import fallback

FIELD_KEYS = ("is_loan_ad", "principal", "in_hand", "fees", "repay_total", "emi_amount",
              "emi_count", "tenure_days", "lender_name", "app_name", "pay_first")
NUMBER_KEYS = ("principal", "in_hand", "fees", "repay_total", "emi_amount", "emi_count",
               "tenure_days")
AMOUNT_KEYS = ("principal", "in_hand", "repay_total", "emi_amount")   # at least one must be read

MSG_NOT_A_LOAN = "Yeh loan ka offer nahi lagta. Loan ke offer ki photo ya message bhejo."
MSG_BAD_PHOTO = "Photo saaf nahi hai, dobara bhejo."
MSG_BAD_TEXT = "Message samajh nahi aaya. Poora loan wala message dobara bhejo."
MSG_BAD_VOICE = "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."

PROMPT = """You read Indian loan advertisements and loan SMS messages for a person who cannot read.
Return ONLY one JSON object, no other text, with exactly these keys:
{"is_loan_ad": true or false,
 "principal": loan amount offered,
 "in_hand": amount the borrower receives, ONLY if the ad states it in words like "you get", "in hand", "disbursed", "credited",
 "fees": processing fee or other charges taken from the loan (a rupee amount, or a percentage like "10%"),
 "repay_total": total amount to repay,
 "emi_amount": one EMI / instalment amount,
 "emi_count": number of EMIs / instalments,
 "tenure_days": loan length exactly as written, with its unit, e.g. "7 days", "2 weeks", "3 months",
 "lender_name": the bank or NBFC named as lender (not the app name),
 "app_name": the app or brand name,
 "pay_first": money the borrower is told to PAY or TRANSFER before getting the loan
   (e.g. "pay Rs 1,499 processing fee to release funds", "pay insurance charges of Rs 1,200 now");
   NOT a fee that is deducted from the loan amount; null if there is none}
Rules: copy numbers exactly as written, including words like "lakh" or "crore";
never calculate, add, subtract or guess a number;
use null for anything not clearly written; is_loan_ad is false for anything that is not a loan offer."""

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
BENGALI_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
# A number with an optional Indian unit after it: "5 lakh", "1.5 lac", "2 crore", "50 hazaar", "5k" (B10).
_UNITS = (("crore", 1e7), ("cr", 1e7), ("करोड़", 1e7), ("करोड", 1e7),
          ("lakh", 1e5), ("lac", 1e5), ("लाख", 1e5),
          ("hazaar", 1e3), ("hazar", 1e3), ("hajar", 1e3), ("thousand", 1e3), ("हज़ार", 1e3),
          ("हजार", 1e3), ("k", 1e3))
_AMOUNT = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(crores?|cr\b|करोड़|करोड|lakhs?|lacs?|लाख|hazaar|hazar|"
                     r"hajar|thousand|हज़ार|हजार|k\b)?", re.IGNORECASE)


def _amount(match: re.Match) -> float:
    """One _AMOUNT match -> rupees: "5 lakh" -> 500000, "5,00,000" -> 500000."""
    number = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").lower()
    for name, factor in _UNITS:
        if unit.startswith(name):
            return number * factor
    return number
_UNIT_DAYS = (("week", 7), ("hafte", 7), ("hafta", 7), ("saptah", 7), ("month", 30),
              ("mahin", 30), ("year", 365), ("saal", 365), ("varsh", 365),
              # B13: Bengali, Marathi and Devanagari Hindi units (days need no entry)
              ("সপ্তাহ", 7), ("सप्ताह", 7), ("आठवड", 7), ("हफ्त", 7), ("মাস", 30), ("महिन", 30), ("महीन", 30),
              ("বছর", 365), ("वर्ष", 365), ("साल", 365))


class NotALoan(Exception):
    """The reader says this is not a loan offer."""
    def __init__(self, text_hi: str = MSG_NOT_A_LOAN):
        super().__init__("not a loan offer")
        self.text_hi = text_hi


class Unreadable(Exception):
    """No reader gave valid fields."""
    def __init__(self, text_hi: str = MSG_BAD_PHOTO):
        super().__init__("unreadable")
        self.text_hi = text_hi


# ---------------------------------------------------------------- clean-up
def strip_fences(raw: str) -> str:
    """Drop <think> blocks and ```json fences; keep the text from the first { to the last }."""
    text = re.sub(r"<think>.*?</think>", "", raw or "", flags=re.DOTALL)
    text = re.sub(r"```(?:json|JSON)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else text


def to_number(value: Any) -> Optional[float]:
    """'Rs 5,000' -> 5000.0, '₹1200/-' -> 1200.0, '₹5 lakh' -> 500000.0, '2 crore' -> 2e7,
    7 -> 7.0, 'null' / '' / 0 / -5 -> None. (Unit words are worked out in code, B10.)"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    match = _AMOUNT.search(str(value).translate(DEVANAGARI_DIGITS))
    if not match:
        return None
    number = _amount(match)
    return number if number > 0 else None


def to_days(value: Any) -> Optional[float]:
    """'7 days' -> 7, '2 weeks' -> 14, '3 months' -> 90, '1 saal' -> 365. Plain numbers are days."""
    if isinstance(value, str):     # days never carry lakh/crore; read the plain number
        match = _NUMBER.search(value.translate(DEVANAGARI_DIGITS))
        number = float(match.group().replace(",", "")) if match else None
        number = number if number and number > 0 else None
    else:
        number = to_number(value)
    if number is None or isinstance(value, (int, float)):
        return number
    text = str(value).lower()
    for unit, days in _UNIT_DAYS:
        if unit in text:
            return number * days
    return number


class Fields(BaseModel):
    """What a reader must return. Text numbers are cleaned before validation."""
    model_config = ConfigDict(extra="ignore")
    is_loan_ad: Optional[bool] = None
    principal: Optional[float] = None
    in_hand: Optional[float] = None
    fees: Optional[float] = None
    repay_total: Optional[float] = None
    emi_amount: Optional[float] = None
    emi_count: Optional[float] = None
    tenure_days: Optional[float] = None
    lender_name: Optional[str] = None
    app_name: Optional[str] = None
    pay_first: Optional[float] = None          # money asked BEFORE the loan (B9): a fraud warning

    @model_validator(mode="before")
    @classmethod
    def clean(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("reader did not return a JSON object")
        data = dict(data)
        fee = data.get("fees")
        principal = to_number(data.get("principal"))
        if isinstance(fee, str) and "%" in fee:          # "10%" of the loan, worked out in code
            pct = to_number(fee)
            data["fees"] = round(principal * pct / 100, 2) if pct and principal else None
        else:
            data["fees"] = to_number(fee)
        data["tenure_days"] = to_days(data.get("tenure_days"))
        for key in ("principal", "in_hand", "repay_total", "emi_amount", "emi_count", "pay_first"):
            data[key] = to_number(data.get(key))
        loan = data.get("is_loan_ad")
        if isinstance(loan, str):
            data["is_loan_ad"] = {"true": True, "yes": True, "false": False, "no": False}.get(loan.strip().lower())
        return data

    @field_validator("lender_name", "app_name", mode="before")
    @classmethod
    def clean_name(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return None if text.lower() in ("", "null", "none", "n/a", "na") else text


def parse(raw: str) -> dict:
    """Reader reply -> the 10 fields. Raises on invalid JSON (that engine then counts as failed)."""
    data = json.loads(strip_fences(raw))
    return Fields.model_validate(data).model_dump()


def _settle_pay_first(fields: dict) -> dict:
    """Once pay_first is accepted, a fee of the same amount is paid separately before the loan,
    not deducted from it, so it leaves the maths (B9). Never done on an unconfirmed claim (B9c)."""
    if fields.get("pay_first") is not None and fields.get("fees") == fields["pay_first"]:
        fields["fees"] = None
    return fields


def _check_loan(fields: dict, unreadable_msg: str) -> None:
    if fields.get("pay_first"):
        return                      # asks for money first: the warning IS the answer (B9)
    if fields["is_loan_ad"] is False:
        raise NotALoan()
    if all(fields[k] is None for k in AMOUNT_KEYS):
        raise Unreadable(unreadable_msg)


# ---------------------------------------------------------------- photo
def extract_from_image(image_bytes: bytes) -> dict:
    """Photo -> fields. Qwen first, Gemini if Qwen fails or returns invalid JSON."""
    try:
        raw, engine, _ = fallback.read_image(image_bytes, PROMPT, check=parse)
    except fallback.EngineError:
        raise Unreadable(MSG_BAD_PHOTO)
    fields = _settle_pay_first(parse(raw))      # photos: only the AI reads them (known limit, B9c)
    _check_loan(fields, MSG_BAD_PHOTO)
    return {"fields": fields, "engines": {"read": engine, "second_read": None}}


OTHER_READER = {"qwen": "gemini", "gemini": "qwen"}


def disputed_fields(first: dict, second: dict, tolerance: float = 1.0) -> list[str]:
    """Number fields the two readings disagree on: values more than Rs 1 apart,
    or one reader saw a number and the other saw none."""
    out = []
    for key in NUMBER_KEYS:
        a, b = first.get(key), second.get(key)
        if (a is None) != (b is None) or (a is not None and abs(a - b) > tolerance):
            out.append(key)
    return out


def second_reading(image_bytes: bytes, first: dict, problems: list[str]) -> tuple[dict, list[str]]:
    """The numbers do not add up, so the OTHER reader reads the photo again (task B6).

    -> (first with engines.second_read filled, names of disputed fields).
    If the other reader fails: second_read stays None and disputed = problems,
    so the fields in the failed sum become "couldn't verify".
    """
    other = OTHER_READER.get(first["engines"]["read"])
    if other is None:
        return first, list(problems)
    try:
        raw, engine, _ = fallback.read_image(image_bytes, PROMPT, engines=(other,), check=parse)
        second = parse(raw)
    except Exception:   # EngineError, or a reply that will not parse: no second opinion
        return first, list(problems)
    result = {"fields": dict(first["fields"]),
              "engines": {**first["engines"], "second_read": engine}}
    return result, disputed_fields(first["fields"], second)


# ---------------------------------------------------------------- text
def _numbers_in(text: str) -> set[float]:
    """Every number written in the message, as written and with its unit ("5 lakh" -> 5 and 500000)."""
    out = set()
    for m in _AMOUNT.finditer(text.translate(DEVANAGARI_DIGITS)):
        out.add(float(m.group(1).replace(",", "")))
        out.add(_amount(m))
    return out


def _words(latin: str, native: tuple[str, ...]) -> re.Pattern:
    """Latin words are matched as whole words (endings allowed where written \\w*); Devanagari and
    Bengali words as plain text, because their vowel signs break the \\b word boundary (B9b).
    Ambiguous short words are left out on purpose: Bengali দিন is both "give" and "day", and
    Hindi/Marathi कर is "tax" but also part of कर्ज (loan)."""
    return re.compile(rf"\b(?:{latin})\b|(?:{'|'.join(map(re.escape, native))})", re.I)


_PAY_VERB = _words(
    r"pay|paid|deposit|transfer|send|bhejo|bhejiye|bhejen|jama|bharo|bhariye|chukao",
    ("भेजो", "भेजें", "भेजिए", "भेज दो", "भेज दें", "जमा करो", "जमा करें", "जमा कीजिए", "भरो", "भरें",
     "भुगतान करें", "भुगतान करो", "ट्रांसफर",                                         # Hindi
     "পাঠান", "পাঠাও", "পাঠিয়ে", "জমা দিন", "জমা করুন", "পেমেন্ট করুন", "ট্রান্সফার",     # Bengali
     "पाठवा", "पाठवावे", "भरा", "भरावे", "जमा करा", "भरणा करा", "पेमेंट करा", "ट्रान्सफर"))  # Marathi
_CHARGE = _words(
    r"fees?|charges?|insurance|registration|processing|gst|tax|token|security|verification|stamp|"
    r"files?|kharcha|shulk",
    ("शुल्क", "फीस", "फी", "चार्ज", "प्रोसेसिंग", "बीमा", "इंश्योरेंस", "रजिस्ट्रेशन", "पंजीकरण", "जीएसटी",
     "टैक्स", "टोकन",                                                                  # Hindi (+ Marathi शुल्क, फी)
     "ফি", "চার্জ", "প্রসেসিং", "বীমা", "ইন্স্যুরেন্স", "রেজিস্ট্রেশন", "নিবন্ধন", "শুল্ক", "জিএসটি",
     "ট্যাক্স",                                                                          # Bengali
     "विमा", "नोंदणी"))                                                                # Marathi
_BEFORE = _words(
    r"releas\w*|before|unlock\w*|activat\w*|to get|disburs\w*|approv\w*|advance|now|immediately|"
    r"turant|pehle|abhi",
    ("पहले", "अभी", "तुरंत", "रिलीज", "पाने के लिए", "मिलने से पहले", "एडवांस",            # Hindi
     "আগে", "এখনই", "এখন", "তাড়াতাড়ি", "রিলিজ", "পেতে", "পাওয়ার জন্য",              # Bengali
     "आधी", "आत्ता", "आता", "त्वरित", "लगेच", "मिळवण्यासाठी", "मिळण्यासाठी"))           # Marathi


def _asks_to_pay(text: str, amount: float) -> bool:
    """B9c: does the sentence that contains this amount tell the reader to pay / send money?
    "Loan Rs 5000 approved. Fee Rs 500." has no pay word, so the AI's "pay 500 first" is not trusted."""
    for sentence in re.split(r"[.!?\n।॥]+", text.translate(DEVANAGARI_DIGITS)):
        amounts = {_amount(m) for m in _AMOUNT.finditer(sentence)}
        if amount in amounts and _PAY_VERB.search(sentence):
            return True
    return False


def pay_first_in_text(text: str) -> Optional[float]:
    """Code backup for B9: a sentence that tells you to PAY a fee or charge to get the loan.

    Needs all three in one sentence: a pay word, a charge word and a before/now word, plus an
    amount. "Pay Rs 5600 in 7 days" (repaying) has no charge word, so it does not count.
    """
    for sentence in re.split(r"[.!?\n।॥]+", text.translate(DEVANAGARI_DIGITS)):    # । ends Hindi/Bengali sentences
        if _PAY_VERB.search(sentence) and _CHARGE.search(sentence) and _BEFORE.search(sentence):
            m = _AMOUNT.search(sentence)
            if m:
                return _amount(m)
    return None


def _drop_unwritten(fields: dict, text: str) -> dict:
    """For text we can check: a number the AI gives that is not in the message was invented.

    fees from a percentage and tenure from weeks/months are worked out in code, so for
    them we check the number as written (the percentage, the 2 in "2 weeks") instead.
    """
    written = _numbers_in(text)
    for key in ("principal", "in_hand", "repay_total", "emi_amount", "emi_count", "pay_first"):
        if fields.get(key) is not None and fields[key] not in written:
            fields[key] = None
    if fields["fees"] is not None and fields["fees"] not in written and "%" not in text:
        fields["fees"] = None
    if fields["tenure_days"] is not None and not written:
        fields["tenure_days"] = None
    return fields


_RS = r"(?:rs\.?|inr|₹|rupees?|rupaye)?\s*"
_AMT = r"(\d[\d,]*(?:\.\d+)?(?:\s*(?:crores?|cr\b|lakhs?|lacs?|hazaar|hazar|thousand|k\b))?)"
_GAP = r"[^\d.!?\n।॥]{0,25}?"       # a label and its number must be in the same sentence (। = danda)
# B13: Bengali, Marathi and Devanagari Hindi labels. In those scripts the currency word comes AFTER
# the number ("5000 টাকার লোন", "10000 रुपयांचे कर्ज", "5000 रुपये का लोन").
_CUR = r"\s*(?:টাকার|টাকা|रुपयांचे|रुपयांचा|रुपयांची|रुपये|रुपए|रुपयों)?\s*(?:का|की|के)?\s*"
_LOAN_NATIVE = r"লোন|ঋণ|कर्ज|लोन|ऋण"
_HAND_NATIVE = r"হাতে|हातात|हाथ में"
_FEE_NATIVE = r"প্রসেসিং ফি|ফি|ফী|শুল্ক|চার্জ|फीस|फी|शुल्क|चार्ज"
_REPAY_NATIVE = r"ফেরত|परत|लौटाने|लौटाना|वापस"
_REGEX = {
    "principal": [rf"(?:loan(?: amount)?|amount|approved|udhaar|karz){_GAP}{_RS}{_AMT}",
                  rf"{_RS}{_AMT}\s*(?:ka\s+)?(?:loan|udhaar|karz)",
                  rf"(?:{_LOAN_NATIVE}){_GAP}{_AMT}",
                  rf"{_AMT}{_CUR}(?:{_LOAN_NATIVE})"],
    "in_hand": [rf"(?:in hand|you get|you will get|disbursed|credited|haath mein|milenge){_GAP}{_RS}{_AMT}",
                rf"{_RS}{_AMT}\s*(?:haath mein|in hand|milenge)",
                rf"(?:{_HAND_NATIVE}){_GAP}{_AMT}",
                rf"{_AMT}{_CUR}(?:{_HAND_NATIVE})"],
    "fees": [rf"(?:processing fee|fees?|charges?|kharcha){_GAP}{_RS}{_AMT}\s*(%)?",
             rf"(?:{_FEE_NATIVE}){_GAP}{_AMT}\s*(%)?"],
    "repay_total": [rf"(?:repay|return|pay back|payback|total|lautana|lautane|chukana|wapas){_GAP}{_RS}{_AMT}",
                    rf"{_RS}{_AMT}\s*(?:lautana|lautane|chukana|wapas|repay)",
                    rf"(?:{_REPAY_NATIVE}){_GAP}{_AMT}",
                    rf"{_AMT}{_CUR}(?:{_REPAY_NATIVE})"],
    "emi": [rf"emi{_GAP}{_RS}{_AMT}\s*(?:x|\*|×)\s*(\d+)"],
    "tenure": [r"(\d+)\s*(days?|din|weeks?|hafte?|months?|mahine?|years?|saal"
               r"|দিন|দিবস|সপ্তাহ|মাস|বছর|दिवस|दिन|सप्ताह|आठवड|हफ्त|महिन|महीन|वर्ष|साल)"],
}


def regex_fields(text: str) -> dict:
    """Backup when the text model is down. Only picks up numbers written next to their label."""
    t = text.lower().translate(DEVANAGARI_DIGITS).translate(BENGALI_DIGITS)
    out = {k: None for k in FIELD_KEYS}

    def first(key):
        """The match that starts earliest in the message, across this key's patterns."""
        found = [m for m in (re.search(p, t) for p in _REGEX[key]) if m]
        return min(found, key=lambda m: m.start()) if found else None

    for key in ("principal", "in_hand", "repay_total"):
        m = first(key)
        out[key] = to_number(m.group(1)) if m else None
    m = first("fees")
    if m:
        value = to_number(m.group(1))
        out["fees"] = (round(out["principal"] * value / 100, 2)
                       if m.group(2) and out["principal"] and value else (None if m.group(2) else value))
    m = first("emi")
    if m:
        out["emi_amount"], out["emi_count"] = to_number(m.group(1)), to_number(m.group(2))
    m = first("tenure")
    if m:
        out["tenure_days"] = to_days(f"{m.group(1)} {m.group(2)}")
    found = any(out[k] is not None for k in AMOUNT_KEYS)
    out["is_loan_ad"] = True if found else None
    return out


def extract_from_text(text: str) -> dict:
    """Pasted SMS -> fields. gpt-oss-20b first; regex if the model is down or answers badly."""
    if not text or not text.strip():
        raise Unreadable(MSG_BAD_TEXT)
    try:
        raw, engine, _ = fallback.read_text(f"{PROMPT}\n\nMESSAGE:\n{text}", check=parse)
        fields = _drop_unwritten(parse(raw), text)
    except fallback.EngineError:
        fields, engine = regex_fields(text), "regex"
    # B9: money asked before the loan. The AI's claim counts only if the message really asks to pay
    # that amount (B9c); the code rule backs it up (and covers the regex path).
    claimed = fields.get("pay_first")
    if claimed is not None and not _asks_to_pay(text, claimed):
        claimed = None                   # e.g. "Loan Rs 5000 approved. Fee Rs 500": a deducted fee
    fields["pay_first"] = claimed or pay_first_in_text(text)
    _settle_pay_first(fields)
    if engine == "regex" and fields["is_loan_ad"] is None and not fields["pay_first"]:
        raise NotALoan()
    _check_loan(fields, MSG_BAD_TEXT)
    return {"fields": fields, "engines": {"read": engine, "second_read": None}}


# ---------------------------------------------------------------- voice note (task D6)
DIGITS_PROMPT = """Rewrite this Hindi/Hinglish message with every number written in full digits.
Examples: "paanch hazaar" -> 5000, "पांच हजार" -> 5000, "chhe hazaar" -> 6000, "saat din" -> 7 din,
"सात दिन" -> 7 दिन, "barah sau" -> 1200, "dedh lakh" -> 150000.
The word "saath"/"साथ" next to "din"/"दिन" means seven (7).
Change nothing else: keep every other word as it is, do not add or calculate anything.
Return only the rewritten message.

MESSAGE:
"""

# "6 हजार" -> 6000, "1.5 lakh" -> 150000, "12 सौ" -> 1200: the multiplier word turned into
# digits by code, like weeks -> days (D31), so the "drop unwritten numbers" rule sees 6000.
_MULTIPLIERS = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hazaar|hazar|hajar|हज़ार|हजार|thousand|lakh|lac|लाख|sau|सौ|hundred)",
    re.IGNORECASE)
_MULTIPLIER_VALUE = {"hazaar": 1000, "hazar": 1000, "hajar": 1000, "हज़ार": 1000, "हजार": 1000,
                     "thousand": 1000, "lakh": 100000, "lac": 100000, "लाख": 100000,
                     "sau": 100, "सौ": 100, "hundred": 100}


def expand_multipliers(text: str) -> str:
    """Digits followed by a multiplier word become one number: "6 हजार" -> "6000"."""
    def full(m: re.Match) -> str:
        value = float(m.group(1)) * _MULTIPLIER_VALUE[m.group(2).lower()]
        return str(int(value)) if value == int(value) else str(value)
    return _MULTIPLIERS.sub(full, text.translate(DEVANAGARI_DIGITS))


def _has_text(raw: str) -> None:
    """check= for read_text: an empty reply counts as a failure of that engine."""
    if not (raw or "").strip():
        raise ValueError("empty rewrite")


def extract_from_voice(audio_bytes: bytes) -> dict:
    """Voice note -> fields, like a pasted SMS (D6, D22, D33).

    Whisper writes down what was said; gpt-oss-20b turns number words into digits (if that
    fails, the raw transcript is used); then extract_from_text reads it, including its rule
    that drops any number not written in the text. engines["listen"] = "whisper".
    """
    try:
        transcript, listen, _ = fallback.transcribe(audio_bytes)
    except fallback.EngineError:
        raise Unreadable(MSG_BAD_VOICE)
    try:
        digits_text, _, _ = fallback.read_text(DIGITS_PROMPT + transcript, check=_has_text)
        digits_text = digits_text.strip()
    except fallback.EngineError:
        digits_text = transcript
    try:
        result = extract_from_text(expand_multipliers(digits_text))
    except Unreadable:
        raise Unreadable(MSG_BAD_VOICE)
    result["engines"]["listen"] = listen
    return result
