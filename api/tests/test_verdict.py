"""Tests for the verdict (task B5). Expected values: docs/PLAN.md, hand-worked table
(verdict column) and "Verdict edges". No test calls the internet."""
import dataclasses

import pytest

from api.core import config
from api.core.verdict import decide

U = "unverified"


def numbers(in_hand, repay, days, apr) -> dict:
    """A CheckResult "numbers" block; U makes a number unverified."""
    def n(value, status):
        return {"value": None, "status": U} if value == U else {"value": value, "status": status}
    return {"in_hand": n(in_hand, "derived"), "repay_total": n(repay, "read"),
            "tenure_days": n(days, "read"), "apr_simple": n(apr, "computed")}


# (row, numbers from docs/PLAN.md, fees read from the ad, expected verdict)
ROWS = [
    (1, numbers(3800, 5000, 7, 1647), 1200, "VERY_COSTLY"),
    (2, numbers(10000, 10250, 30, 30), None, "USUAL"),
    (3, numbers(10000, 10600, 30, 73), None, "COSTLY"),
    (4, numbers(20000, 24000, 360, 20), None, "USUAL"),
    (5, numbers(20000, 24000, 360, 20), None, "USUAL"),
    (6, numbers(9900, 10000, 30, 12), 100, "VERY_COSTLY"),    # fee rule
    (7, numbers(4500, 5600, 7, 1275), None, "VERY_COSTLY"),
    (8, numbers(3800, 5000, U, U), 1200, "CANNOT_SAY"),       # days missing
    (9, numbers(3800, 5000, U, U), 1200, "CANNOT_SAY"),       # zero days
    (10, numbers(3800, U, 7, U), 1200, "CANNOT_SAY"),         # repay disputed
]


@pytest.mark.parametrize("row, nums, fees, expected", ROWS, ids=[f"row{r[0]}" for r in ROWS])
def test_plan_table(row, nums, fees, expected):
    assert decide(nums, fees) == expected


@pytest.mark.parametrize("apr, expected", [(35, "USUAL"), (36, "COSTLY"),
                                           (100, "COSTLY"), (101, "VERY_COSTLY")])
def test_band_edges(apr, expected):
    assert decide(numbers(10000, 10500, 60, apr), None) == expected


def test_fee_rule_needs_a_short_loan():
    assert decide(numbers(9900, 10000, 30, 12), 100) == "VERY_COSTLY"   # 30 days: rule applies
    assert decide(numbers(9900, 10000, 31, 12), 100) == "USUAL"         # 31 days: it does not
    assert decide(numbers(9900, 10000, 30, 12), 0) == "USUAL"           # no fee charged


def test_unverified_in_hand_is_cannot_say():
    assert decide(numbers(U, 5000, 7, 1647), 1200) == "CANNOT_SAY"
    assert decide({}, None) == "CANNOT_SAY"


def test_threshold_change_needs_no_code_change(monkeypatch):
    row2 = ROWS[1][1]
    assert decide(row2, None) == "USUAL"
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, band_costly_apr=20))
    assert decide(row2, None) == "COSTLY"
