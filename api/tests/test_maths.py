"""Tests for the rupee maths (tasks B3, B4).

Expected values are the hand-worked table in docs/PLAN.md ("Tests with hand-worked
values"), copied exactly. No test calls the internet.
"""
import pytest

from api.core.maths import compute, cross_check, fill_gaps

U = "unverified"


def ad(**fields) -> dict:
    """The fields extract.py returns; anything not given was not on the ad."""
    base = dict.fromkeys(["is_loan_ad", "principal", "in_hand", "fees", "repay_total",
                          "emi_amount", "emi_count", "tenure_days", "lender_name", "app_name"])
    base.update(fields)
    return base


# Rows 1-10 of docs/PLAN.md:
# (row, fields, disputed, in_hand, repay_total, extra, per_day, apr_simple)
# in_hand / repay_total are (value, status); U means unverified.
ROWS = [
    (1, ad(principal=5000, fees=1200, repay_total=5000, tenure_days=7), [],
     (3800, "derived"), (5000, "read"), 1200, 171, 1647),
    (2, ad(principal=10000, repay_total=10250, tenure_days=30), [],
     (10000, "derived"), (10250, "read"), 250, 8, 30),
    (3, ad(principal=10000, repay_total=10600, tenure_days=30), [],
     (10000, "derived"), (10600, "read"), 600, 20, 73),
    (4, ad(principal=20000, repay_total=24000, emi_amount=2000, emi_count=12, tenure_days=360), [],
     (20000, "derived"), (24000, "read"), 4000, 11, 20),
    (5, ad(principal=20000, emi_amount=2000, emi_count=12, tenure_days=360), [],
     (20000, "derived"), (24000, "derived"), 4000, 11, 20),
    (6, ad(principal=10000, fees=100, repay_total=10000, tenure_days=30), [],
     (9900, "derived"), (10000, "read"), 100, 3, 12),
    (7, ad(principal=5000, in_hand=4500, repay_total=5600, tenure_days=7), [],
     (4500, "read"), (5600, "read"), 1100, 157, 1275),
    (8, ad(principal=5000, fees=1200, repay_total=5000), [],
     (3800, "derived"), (5000, "read"), 1200, U, U),
    (9, ad(principal=5000, fees=1200, repay_total=5000, tenure_days=0), [],
     (3800, "derived"), (5000, "read"), 1200, U, U),
    (10, ad(principal=5000, fees=1200, repay_total=5000, tenure_days=7), ["repay_total"],
     (3800, "derived"), U, U, U, U),
]


def expect(value) -> dict:
    """Turn a table cell into the number dict the API sends."""
    if value == U:
        return {"value": None, "status": U}
    if isinstance(value, tuple):
        return {"value": value[0], "status": value[1]}
    return {"value": value, "status": "computed"}


@pytest.mark.parametrize("row, fields, disputed, in_hand, repay, extra, per_day, apr",
                         ROWS, ids=[f"row{r[0]}" for r in ROWS])
def test_plan_table(row, fields, disputed, in_hand, repay, extra, per_day, apr):
    result = compute(fill_gaps(fields, disputed))
    assert result["in_hand"] == expect(in_hand)
    assert result["repay_total"] == expect(repay)
    assert result["extra"] == expect(extra)
    assert result["per_day"] == expect(per_day)
    assert result["apr_simple"] == expect(apr)
    assert set(result) == {"in_hand", "repay_total", "tenure_days", "extra", "per_day", "apr_simple"}


def test_days_status():
    assert fill_gaps(ROWS[0][1])["tenure_days"] == {"value": 7, "status": "read"}
    assert fill_gaps(ROWS[7][1])["tenure_days"] == expect(U)   # row 8: missing
    assert fill_gaps(ROWS[8][1])["tenure_days"] == expect(U)   # row 9: zero


# --- cross-check (docs/PLAN.md "More tests") ---

def test_cross_check_in_hand_mismatch():
    assert cross_check(ad(principal=5000, fees=1200, in_hand=4000)) == ["principal", "fees", "in_hand"]


def test_cross_check_within_one_rupee():
    assert cross_check(ad(principal=5000, fees=1200, in_hand=3801)) == []


def test_cross_check_emi_mismatch():
    assert cross_check(ad(emi_amount=2000, emi_count=12, repay_total=25000)) == \
        ["emi_amount", "emi_count", "repay_total"]


def test_cross_check_needs_all_three_numbers():
    assert cross_check(ad(principal=5000, repay_total=5000)) == []


# --- never a verified wrong number ---

def test_self_contradicting_ad_is_unverified():
    # Both readers see 5000 / 1200 / in_hand 4000: in_hand must not be shown as verified.
    result = compute(fill_gaps(ad(principal=5000, fees=1200, in_hand=4000,
                                  repay_total=5000, tenure_days=7)))
    assert result["in_hand"] == expect(U)
    assert result["extra"] == expect(U)


def test_disputed_fee_is_not_treated_as_no_fee():
    result = fill_gaps(ad(principal=5000, fees=1200, repay_total=5000, tenure_days=7), ["fees"])
    assert result["in_hand"] == expect(U)


def test_repaying_less_than_in_hand_is_unverified():
    result = compute(fill_gaps(ad(in_hand=5000, repay_total=4000, tenure_days=7)))
    for key in ("extra", "per_day", "apr_simple"):
        assert result[key] == expect(U)


def test_empty_input_does_not_crash():
    result = compute(fill_gaps(ad()))
    assert all(result[k] == expect(U) for k in result)
    assert compute({})["extra"] == expect(U)
