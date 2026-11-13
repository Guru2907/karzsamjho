"""Cost band and final verdict (task B5): USUAL / COSTLY / VERY_COSTLY / CANNOT_SAY.

Rules: docs/PLAN.md, "Rules inside the maths". The thresholds are our own rule of
thumb, NOT an RBI limit, and live in config.py (band_costly_apr,
band_very_costly_apr, short_loan_days). They are read on every call, so changing a
threshold changes the verdict without touching this file.
"""
from api.core import config

KEY_NUMBERS = ("in_hand", "repay_total", "tenure_days", "apr_simple")


def _value(numbers: dict, key: str) -> float | None:
    """The value of a verified number, or None if it is missing or unverified."""
    item = numbers.get(key)
    if not isinstance(item, dict) or item.get("status") == "unverified":
        return None
    value = item.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def decide(numbers: dict, fees: float | None) -> str:
    """numbers = the output of maths.compute(); fees = the fee read from the ad, or None
    (None also when the fee was disputed)."""
    s = config.settings
    values = {key: _value(numbers, key) for key in KEY_NUMBERS}
    if any(v is None for v in values.values()):
        return "CANNOT_SAY"

    apr, days = values["apr_simple"], values["tenure_days"]
    fee_upfront_on_short_loan = fees is not None and fees > 0 and days <= s.short_loan_days
    if apr > s.band_very_costly_apr or fee_upfront_on_short_loan:
        return "VERY_COSTLY"
    if apr >= s.band_costly_apr:
        return "COSTLY"
    return "USUAL"
