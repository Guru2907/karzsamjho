"""C1: RBI directory match (name + website). A small made-up directory; no real company names."""
import dataclasses
import json

import pytest

from api import main
from api.core import config, fallback, lender

CSV = """dla_name,regulated_entity,website,list_date
QuickRupee,Alpha Finance Pvt Ltd,https://www.quickrupee.in,2026-11-10
RupeeFast Credit,Beta Capital Ltd,https://play.google.com/store/apps/details?id=com.rupeefast.app,2026-11-10
CashNow24,Gamma NBFC Ltd,,2026-11-10
Money View Test,Delta Fincorp Ltd,moneyviewtest.co.in,2026-11-10
"""


@pytest.fixture
def directory(monkeypatch, tmp_path):
    path = tmp_path / "rbi_dla.csv"
    path.write_text(CSV, encoding="utf-8")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, rbi_dla_path=str(path)))
    return path


@pytest.mark.parametrize("name, match, closest", [
    ("QuickRupee", "FOUND", "QuickRupee (Alpha Finance Pvt Ltd)"),
    ("quick rupee", "FOUND", "QuickRupee (Alpha Finance Pvt Ltd)"),
    ("Quick Rupee Loan App", "FOUND", "QuickRupee (Alpha Finance Pvt Ltd)"),     # generic words stripped
    ("QuikRupee", "FOUND", "QuickRupee (Alpha Finance Pvt Ltd)"),                # small typo
    ("Alpha Finance", "FOUND", "QuickRupee (Alpha Finance Pvt Ltd)"),            # the lender itself named
    ("CashNow", "SIMILAR", "CashNow24 (Gamma NBFC Ltd)"),                        # close, not the same
    ("ZapCash Express", "NOT_FOUND", None),                                      # made-up app
])
def test_name_bands(directory, name, match, closest):
    r = lender.match_lender(name)
    assert (r["match"], r["closest"]) == (match, closest)
    assert r["name_read"] == name and r["list_date"] == "2026-11-10"
    assert isinstance(r["score"], float)


def test_link_to_a_listed_website_is_found_even_without_a_name(directory):
    r = lender.match_lender(None, "Apply now: https://quickrupee.in/apply?ref=sms")
    assert r["match"] == "FOUND" and r["closest"].startswith("QuickRupee") and r["score"] == 100


def test_play_store_link_and_co_in_domain(directory):
    play = "https://play.google.com/store/apps/details?id=com.rupeefast.app&hl=en"
    assert lender.match_lender(None, f"Download {play}")["closest"].startswith("RupeeFast Credit")
    assert lender.match_lender(None, "visit moneyviewtest.co.in today")["match"] == "FOUND"


def test_clone_name_with_a_different_link_is_only_similar(directory):
    # the name matches QuickRupee, but the link goes to another site: a possible clone
    r = lender.match_lender("QuickRupee", "Loan in 2 min: http://quickrupee-loans.xyz/get")
    assert r["match"] == "SIMILAR" and r["closest"].startswith("QuickRupee")


def test_unknown_link_and_unknown_name(directory):
    r = lender.match_lender("ZapCash", "http://zapcash.top/apply")
    assert r["match"] == "NOT_FOUND" and r["closest"] is None


def test_nothing_to_check_or_empty_directory_is_not_checked(directory, monkeypatch, tmp_path):
    assert lender.match_lender(None)["match"] is None                     # nothing was read
    empty = tmp_path / "empty.csv"
    empty.write_text("dla_name,regulated_entity,list_date\n", encoding="utf-8")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, rbi_dla_path=str(empty)))
    r = lender.match_lender("QuickRupee")
    assert r["match"] is None and r["list_date"] is None                  # never "not found" on no data


def test_csv_without_website_column_still_works(monkeypatch, tmp_path):
    path = tmp_path / "old.csv"
    path.write_text("dla_name,regulated_entity,list_date\nQuickRupee,Alpha Finance Pvt Ltd,2026-11-01\n",
                    encoding="utf-8")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, rbi_dla_path=str(path)))
    assert lender.match_lender("QuickRupee")["match"] == "FOUND"


def test_directory_reloads_when_the_file_changes(directory):
    assert lender.match_lender("ZapCash Express")["match"] == "NOT_FOUND"
    import os, time
    directory.write_text(CSV + "ZapCash Express,Epsilon Finance Ltd,,2026-11-12\n", encoding="utf-8")
    os.utime(directory, (time.time() + 5, time.time() + 5))
    r = lender.match_lender("ZapCash Express")
    assert r["match"] == "FOUND" and r["list_date"] == "2026-11-12"


def test_sites_in_ignores_amounts_and_images():
    assert lender.sites_in("Loan Rs 5,000.00 at www.quickrupee.in now, see pic.jpg") == ["quickrupee.in"]


# ---------------------------------------------------------------- through the API
def test_check_result_carries_the_lender_match(client, directory, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, audio_dir=str(tmp_path / "a"), cache_dir=str(tmp_path / "c"), voice_enabled=False))
    monkeypatch.setattr(main, "CHECKS", {})

    def read_text(prompt, check=None):
        return json.dumps({"is_loan_ad": True, "principal": 5000, "fees": 500, "repay_total": 5600,
                           "tenure_days": 7, "app_name": "QuickRupee"}), "gpt-oss-20b", 0.5
    monkeypatch.setattr(fallback, "read_text", read_text)
    body = client.post("/api/checks", json={
        "text": "QuickRupee: Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days. https://quickrupee.in"}).json()
    assert body["lender"]["match"] == "FOUND"
    assert body["lender"]["closest"] == "QuickRupee (Alpha Finance Pvt Ltd)"
    assert body["lender"]["list_date"] == "2026-11-10"
    for word in ("safe", "illegal", "fake"):
        assert word not in json.dumps(body["lender"]).lower()


# ---- RBI's real directory (api/data/rbi_dla.csv, built by scripts/build_ledger.py, G4) --------------
# Public data from rbi.org.in. These tests only check the match TYPE, so a newer list keeps them valid
# unless an app is added or removed. They guard against the partial-match bug: invented names must never
# come back FOUND (the worst mistake this check can make on stage).
REAL_LIST = config.ROOT / "api" / "data" / "rbi_dla.csv"


@pytest.fixture
def real_list(monkeypatch):
    if REAL_LIST.stat().st_size < 1000:
        pytest.skip("RBI's real list is not in api/data/rbi_dla.csv")
    monkeypatch.setattr(config, "settings", dataclasses.replace(config.settings, rbi_dla_path=str(REAL_LIST)))


@pytest.mark.parametrize("name, match", [
    ("KreditBee", "FOUND"),
    ("Kredit Bee Loan App", "FOUND"),      # generic words removed
    ("KreditBea", "SIMILAR"),              # one letter changed
    # invented names that the old partial matching wrongly called FOUND or SIMILAR
    ("Tez Kanak", "NOT_FOUND"),
    ("Kanak Credit", "NOT_FOUND"),
    ("Phatafat Kosh", "NOT_FOUND"),
    ("Zxqv Paisa", "NOT_FOUND"),
    # the demo ads' names (D49): must stay NOT_FOUND
    ("SmartEMI", "NOT_FOUND"),
    ("Galla Go", "NOT_FOUND"),
    ("Jaldi Gullak", "NOT_FOUND"),
])
def test_real_rbi_list_bands(real_list, name, match):
    assert lender.match_lender(name)["match"] == match


def test_real_rbi_list_play_store_link(real_list):
    r = lender.match_lender(None, "Download https://play.google.com/store/apps/details?id=com.kreditbee.android")
    assert r["match"] == "FOUND" and r["closest"].lower().startswith("kreditbee")


def test_real_rbi_list_has_no_placeholder_names(real_list):
    rows, list_date = lender.directory()
    names = {r["dla_name"].strip().lower() for r in rows}
    assert not names & {"na", "n.a.", "nil", "nill", "none", "not applicable", "0", "1"}
    assert list_date and len(rows) > 1000


# ---- C3 / D51: NBFC list + cancelled-registration list (made-up rows) ------------------------------
NBFC_CSV = """nbfc_name,former_name,cin,regional_office,classification,list_date,source_url
Alpha Finance Private Limited,Old Alpha Leasing Ltd,U1,Mumbai,ICC,2026-09-30,https://example.org/nbfc.xlsx
"""
WATCH_CSV = """name,website,list_name,source_type,source_url,source_date,note
Dhokha Fincap Pvt. Ltd.,,RBI: registration cancelled,official,https://example.org/cancelled.xlsx,2026-09-30,Cancelled
Rajmandir Estates (P) Ltd,,RBI: registration cancelled,official,https://example.org/cancelled.xlsx,2026-09-30,
"""


@pytest.fixture
def lists(directory, monkeypatch, tmp_path):
    (tmp_path / "nbfc.csv").write_text(NBFC_CSV, encoding="utf-8")
    (tmp_path / "watch.csv").write_text(WATCH_CSV, encoding="utf-8")
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, rbi_nbfc_path=str(tmp_path / "nbfc.csv"), watch_list_path=str(tmp_path / "watch.csv")))


@pytest.mark.parametrize("name", ["Dhokha Fincap Pvt. Ltd.", "dhokha fincap", "DHOKHA FINCAP LIMITED",
                                  "Rajmandir Estates Pvt Ltd"])
def test_cancelled_registration_warns_on_the_exact_name(lists, name):
    r = lender.match_lender(name)
    assert r["warning"]["list"] == "RBI: registration cancelled" and r["warning"]["date"] == "2026-09-30"
    assert r["warning"]["source"].startswith("https://") and r["nbfc"] is None
    assert r["match"] == "NOT_FOUND"                     # the app list result keeps its meaning


@pytest.mark.parametrize("name", ["Dhokha Fincaps", "Dhoka Fincap", "Dhokha", "QuickRupee"])
def test_a_similar_name_is_never_warned(lists, name):
    assert lender.match_lender(name)["warning"] is None   # exact only: never tell off a look-alike


def test_nbfc_found_by_name_former_name_or_the_lender_behind_an_app(lists):
    assert lender.match_lender("Alpha Finance Pvt Ltd")["nbfc"]["name"] == "Alpha Finance Private Limited"
    assert lender.match_lender("Old Alpha Leasing")["nbfc"]["list_date"] == "2026-09-30"
    r = lender.match_lender("QuickRupee")                # FOUND app whose lender is Alpha Finance
    assert r["match"] == "FOUND" and r["nbfc"]["name"] == "Alpha Finance Private Limited"
    assert lender.match_lender("Zeta Credit")["nbfc"] is None


def test_without_the_list_files_nbfc_and_warning_are_null(directory):
    r = lender.match_lender("Dhokha Fincap Pvt. Ltd.")   # conftest points both paths at missing files
    assert r["nbfc"] is None and r["warning"] is None


def test_real_cancelled_list_warns_alok_auto_credit(real_list, monkeypatch):
    monkeypatch.setattr(config, "settings", dataclasses.replace(
        config.settings, watch_list_path=str(config.ROOT / "api" / "data" / "watch_list.csv")))
    assert lender.match_lender("Alok Auto Credit Pvt. Ltd.")["warning"]["date"] == "2026-09-30"
    assert lender.match_lender("Alok Auto Credits")["warning"] is None
