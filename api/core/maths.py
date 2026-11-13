"""Rupee maths in plain Python (tasks B3, B4). No AI is called from this file.

Flow: extract.py reads the fields -> cross_check() finds contradictions ->
fill_gaps() builds the three input numbers -> compute() adds the three results.

Every number is a dict {"value": number or None, "status": "read" | "derived" |
"computed" | "unverified"}. A number we cannot stand behind is "unverified" with
value None; it is never guessed and never raises a division error.
"""
from api.core.config import settings

UNVERIFIED = {"value": None, "status": "unverified"}


def _num(value) -> float | None:
    """A usable number, or None for anything missing or not a number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value or value in (float("inf"), float("-inf")):  # NaN or infinity
        return None
    return float(value)


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
    """Names of fields that contradict each other; [] means consistent.

    A check runs only when all of its numbers were read. Tolerance is Rs 1
    (settings.crosscheck_tolerance_rs).
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


def fill_gaps(fields: dict) -> dict:
    """Build in_hand, repay_total and tenure_days from the fields that were read.

    - a number written on the ad keeps status "read";
    - a missing in_hand is principal - fees, status "derived";
    - a missing repay_total is emi_amount * emi_count, status "derived";
    - no fee and no in-hand amount on the ad -> in_hand is "unverified" (we do
      not assume the fee is zero);
    - anything cross_check() flags is "unverified", so a contradictory ad can
      never show a verified number.
    """
    bad = set(cross_check(fields))
    f = {k: _num(fields.get(k)) for k in (
        "principal", "fees", "in_hand", "repay_total", "emi_amount", "emi_count", "tenure_days")}

    def number(value: float | None, status: str) -> dict:
        if value is None or value <= 0:
            return dict(UNVERIFIED)
        return {"value": _tidy(value), "status": status}

    if "in_hand" in bad:
        in_hand = dict(UNVERIFIED)
    elif f["in_hand"] is not None:
        in_hand = number(f["in_hand"], "read")
    elif f["principal"] is not None and f["fees"] is not None:
        in_hand = number(f["principal"] - f["fees"], "derived")
    else:
        in_hand = dict(UNVERIFIED)

    if "repay_total" in bad:
        repay_total = dict(UNVERIFIED)
    elif f["repay_total"] is not None:
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
    """Add extra, per_day and apr_simple to the output of fill_gaps().

    The result is CheckResult["numbers"]. apr_simple is a percentage (1647 means
    1,647% a year). If an input is unverified, every output that depends on it
    is unverified. Repaying less than the in-hand amount is treated as a misread.
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
        return {"value": round(value), "status": "computed"}

    has_days = extra is not None and days is not None and days > 0
    out["extra"] = computed(extra)
    out["per_day"] = computed(extra / days if has_days else None)
    out["apr_simple"] = computed(extra / in_hand * 365 / days * 100 if has_days else None)
    return out
