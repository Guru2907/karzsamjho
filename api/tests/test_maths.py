"""Tests for the rupee maths (tasks B3, B4). Expected values were written by hand."""
from api.core.maths import compute, cross_check, fill_gaps

UNVERIFIED = {"value": None, "status": "unverified"}


def ad(**fields) -> dict:
    """The fields extract.py returns; anything not given was not on the ad."""
    base = dict.fromkeys(["is_loan_ad", "principal", "in_hand", "fees", "repay_total",
                          "emi_amount", "emi_count", "tenure_days", "lender_name", "app_name"])
    base.update(fields)
    return base


# --- fill gaps ---

def test_fee_upfront_derives_in_hand():
    numbers = fill_gaps(ad(principal=5000, fees=1200, repay_total=5000, tenure_days=7))
    assert numbers["in_hand"] == {"value": 3800, "status": "derived"}
    assert numbers["repay_total"] == {"value": 5000, "status": "read"}
    assert numbers["tenure_days"] == {"value": 7, "status": "read"}


def test_stated_in_hand_that_agrees_stays_read():
    numbers = fill_gaps(ad(principal=5000, fees=1200, in_hand=3800, repay_total=5000, tenure_days=7))
    assert numbers["in_hand"] == {"value": 3800, "status": "read"}


def test_emi_fills_missing_repay_total():
    numbers = fill_gaps(ad(principal=5000, fees=0, emi_amount=1500, emi_count=4, tenure_days=28))
    assert numbers["repay_total"] == {"value": 6000, "status": "derived"}
    assert numbers["in_hand"] == {"value": 5000, "status": "derived"}


def test_no_fee_and_no_in_hand_is_unverified_not_guessed():
    numbers = fill_gaps(ad(principal=10000, repay_total=10500, tenure_days=30))
    assert numbers["in_hand"] == UNVERIFIED
    assert compute(numbers)["extra"] == UNVERIFIED


# --- cross-check ---

def test_in_hand_mismatch_is_flagged():
    fields = ad(principal=5000, fees=1200, in_hand=4500, repay_total=5000, tenure_days=7)
    assert cross_check(fields) == ["principal", "fees", "in_hand"]


def test_emi_mismatch_is_flagged():
    fields = ad(emi_amount=1500, emi_count=4, repay_total=7000)
    assert cross_check(fields) == ["emi_amount", "emi_count", "repay_total"]


def test_within_one_rupee_is_consistent():
    assert cross_check(ad(principal=5000, fees=1200, in_hand=3801)) == []
    assert cross_check(ad(principal=5000, fees=1200, in_hand=3802)) != []
    assert cross_check(ad(principal=5000, repay_total=5000)) == []  # nothing to compare


def test_contradictory_ad_never_shows_a_verified_number():
    fields = ad(principal=5000, fees=1200, in_hand=4500, repay_total=5000, tenure_days=7)
    result = compute(fill_gaps(fields))
    assert result["in_hand"] == UNVERIFIED
    for key in ("extra", "per_day", "apr_simple"):
        assert result[key] == UNVERIFIED


# --- maths ---

def test_seven_day_loan_numbers():
    result = compute(fill_gaps(ad(principal=5000, fees=1200, repay_total=5000, tenure_days=7)))
    assert result["extra"] == {"value": 1200, "status": "computed"}
    assert result["per_day"] == {"value": 171, "status": "computed"}      # 1200 / 7 = 171.4
    assert result["apr_simple"] == {"value": 1647, "status": "computed"}  # 1200/3800 * 365/7 = 1646.6%
    assert set(result) == {"in_hand", "repay_total", "tenure_days", "extra", "per_day", "apr_simple"}


def test_normal_thirty_day_loan():
    result = compute(fill_gaps(ad(principal=10000, fees=500, repay_total=10300, tenure_days=30)))
    assert result["in_hand"]["value"] == 9500
    assert result["extra"]["value"] == 800
    assert result["per_day"]["value"] == 27       # 800 / 30 = 26.7
    assert result["apr_simple"]["value"] == 102   # 800/9500 * 365/30 = 102.5%


def test_missing_repay_total_makes_outputs_unverified():
    result = compute(fill_gaps(ad(principal=5000, fees=1200, tenure_days=7)))
    assert result["in_hand"]["value"] == 3800
    for key in ("repay_total", "extra", "per_day", "apr_simple"):
        assert result[key] == UNVERIFIED


def test_zero_days_is_unverified_not_a_crash():
    result = compute(fill_gaps(ad(principal=5000, fees=1200, repay_total=5000, tenure_days=0)))
    assert result["tenure_days"] == UNVERIFIED
    assert result["extra"] == {"value": 1200, "status": "computed"}
    assert result["per_day"] == UNVERIFIED
    assert result["apr_simple"] == UNVERIFIED


def test_missing_days_is_unverified_not_a_crash():
    result = compute(fill_gaps(ad(principal=5000, fees=1200, repay_total=5000)))
    assert result["extra"]["value"] == 1200
    assert result["per_day"] == UNVERIFIED
    assert result["apr_simple"] == UNVERIFIED
    assert compute({})["extra"] == UNVERIFIED  # empty input does not crash either


def test_repaying_less_than_in_hand_is_a_misread():
    result = compute(fill_gaps(ad(in_hand=5000, repay_total=4000, tenure_days=7)))
    for key in ("extra", "per_day", "apr_simple"):
        assert result[key] == UNVERIFIED
