"""Rupee maths in plain Python (tasks B3, B4). No AI is called from this file.

Rules: docs/PLAN.md, "Rules inside the maths". Flow in api/main.py:
cross_check(fields) -> (second reading) -> compute(fill_gaps(fields, disputed)).

Every number is a dict {"value": number or None, "status": "read" | "derived" |
"computed" | "unverified"}. A number we cannot stand behind is "unverified" with
value None; it is never guessed and never raises a division error.
"""
import math

from api.core.config import settings

UNVERIFIED = {"value": None, "status": "unverified"}


def _num(value) -> float | None:
    """A usable number, or None for anything missing or not a number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return float(value)


def _whole(value: float) -> int:
    """Round to a whole rupee, halves go up (171.5 -> 172), unlike Python's round()."""
    return math.floor(value + 0.5)


def _tidy(value: float) -> int | float:
    """3800.0 -> 3800; keep paise only when they are really there."""
    rounded = round(value, 2)
    return int(rounded) if rounded == int(rounded) else rounded


def _known(numbers: dict, key: str) -> float | None:
    """The value of a number we can trust, or None if it is missing or unverified."""
    item = numbers.get(key)
    if not isinstance(item, dict) or item.get("status") == "unverified":
        return None
    return _num(item.get("value"))


def cross_check(fields: dict) -> list[str]:
    """Names of the fields in every sum that fails by more than Rs 1; [] when all is fine.

    A sum is only checked when all three of its numbers are present.
    """
    tolerance = settings.crosscheck_tolerance_rs
    bad: list[str] = []

    principal, fees, in_hand = (_num(fields.get(k)) for k in ("principal", "fees", "in_hand"))
    if None not in (principal, fees, in_hand) and abs(principal - fees - in_hand) > tolerance:
        bad += ["principal", "fees", "in_hand"]

    emi_amount, emi_count, repay_total = (
        _num(fields.get(k)) for k in ("emi_amount", "emi_count", "repay_total"))
    if None not in (emi_amount, emi_count, repay_total) \
            and abs(emi_amount * emi_count - repay_total) > tolerance:
        bad += ["emi_amount", "emi_count", "repay_total"]

    return bad


def fill_gaps(fields: dict, disputed: list[str] = ()) -> dict:
    """Build in_hand, repay_total and tenure_days. A field in `disputed` counts as missing.

    in_hand:     principal - fees ("derived") > written in_hand ("read")
                 > principal alone when the ad wrote no fee ("derived") > unverified
    repay_total: written ("read") > emi_amount x emi_count ("derived") > unverified
    tenure_days: written and above 0 ("read") > unverified

    Safety net: a sum that cross_check() still finds broken is treated as disputed
    too, so a self-contradicting ad never shows a verified number.
    """
    gone = set(disputed) | set(cross_check(fields))
    f = {k: (None if k in gone else _num(fields.get(k))) for k in (
        "principal", "fees", "in_hand", "repay_total", "emi_amount", "emi_count", "tenure_days")}

    def number(value: float | None, status: str) -> dict:
        if value is None or value <= 0:
            return dict(UNVERIFIED)
        return {"value": _tidy(value), "status": status}

    if f["principal"] is not None and f["fees"] is not None:
        in_hand = number(f["principal"] - f["fees"], "derived")
    elif f["in_hand"] is not None:
        in_hand = number(f["in_hand"], "read")
    elif f["principal"] is not None and "fees" not in gone:
        # No fee written on the ad. A fee that was written but disputed is not "no fee".
        in_hand = number(f["principal"], "derived")
    else:
        in_hand = dict(UNVERIFIED)

    if f["repay_total"] is not None:
        repay_total = number(f["repay_total"], "read")
    elif f["emi_amount"] is not None and f["emi_count"] is not None:
        repay_total = number(f["emi_amount"] * f["emi_count"], "derived")
    else:
        repay_total = dict(UNVERIFIED)

    return {
        "in_hand": in_hand,
        "repay_total": repay_total,
        "tenure_days": number(f["tenure_days"], "read"),
    }


def compute(numbers: dict) -> dict:
    """Add extra, per_day and apr_simple: the "numbers" block of CheckResult.

    apr_simple is a percentage (1647 means 1,647% a year). All three are whole
    numbers. An unverified input, or extra below 0, makes the outputs that need
    it unverified.
    """
    out = {key: dict(numbers.get(key) or UNVERIFIED)
           for key in ("in_hand", "repay_total", "tenure_days")}
    in_hand = _known(out, "in_hand")
    repay_total = _known(out, "repay_total")
    days = _known(out, "tenure_days")

    extra = None
    if in_hand is not None and repay_total is not None and in_hand > 0 and repay_total >= in_hand:
        extra = repay_total - in_hand

    def computed(value: float | None) -> dict:
        if value is None:
            return dict(UNVERIFIED)
        return {"value": _whole(value), "status": "computed"}

    has_days = extra is not None and days is not None and days > 0
    out["extra"] = computed(extra)
    out["per_day"] = computed(extra / days if has_days else None)
    out["apr_simple"] = computed(extra / in_hand * 365 / days * 100 if has_days else None)
    return out
