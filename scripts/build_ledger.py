"""
scripts/build_ledger.py
Rebuilds the three lender-ledger CSVs from the official RBI raw files in api/data/raw/.

Outputs:
  api/data/rbi_dla.csv          RBI Digital Lending Apps directory (G4)
  api/data/rbi_nbfc.csv         RBI registered NBFCs (C3 data)
  api/data/watch_list.csv       Cancelled-registration watch list (C3 data)

Requirements (not in api/requirements.txt -- for data rebuild only):
  pip install openpyxl

Usage:
  python scripts/build_ledger.py

HARD RULES baked in:
  - Never writes "illegal", "fake", "fraud", "scam company" or "safe" about a lender.
  - No addresses, emails or phone numbers in any output CSV.
  - Every row comes from the raw files; nothing is typed from memory.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl is required: pip install openpyxl")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "api" / "data" / "raw"
OUT = ROOT / "api" / "data"

# ---------------------------------------------------------------------------
# Shared text cleaning
# ---------------------------------------------------------------------------

def _clean(val) -> str:
    """str(), strip, collapse whitespace, remove invisible chars, replace U+FFFD."""
    if val is None:
        return ""
    s = str(val)
    s = s.replace("\u200e", "").replace("\u200b", "").replace("\ufffd", "-")
    s = re.sub(r"[\r\n\t]+", " ", s)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


# ---------------------------------------------------------------------------
# STEP 1 — rbi_dla.csv
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"https?://\S+", re.I)
_PLAY_ID_RE = re.compile(r"[?&]id=([A-Za-z0-9_.]+)", re.I)


def _extract_website(link_cell: str) -> str:
    """Return a usable website from the 'Link to DLA' cell, or ''."""
    if not link_cell:
        return ""
    # find the first URL in the cell
    m = _URL_RE.search(link_cell)
    if not m:
        return ""
    url = m.group(0).rstrip(".,;)")

    # Play Store with ?id= -> keep
    if "play.google.com" in url.lower():
        if _PLAY_ID_RE.search(url):
            return url
        return ""  # Play Store link without id=

    # Apple App Store -> exclude
    if "apps.apple.com" in url.lower():
        return ""

    # email -> exclude
    if url.lower().startswith("mailto:"):
        return ""

    # leading ? junk (seen in data)
    url = url.lstrip("?")
    if not url.startswith("http"):
        return ""

    return url


def build_rbi_dla(list_date: str) -> int:
    wb = openpyxl.load_workbook(RAW / "rbi_dla.xlsx", data_only=True)
    ws = wb["Digital Lending App"]

    # find header row: row whose 2nd cell is "Sr. No"
    header_row_idx = None
    rows = list(ws.iter_rows(values_only=True))
    for i, row in enumerate(rows):
        if _clean(row[1]).lower() == "sr. no":
            header_row_idx = i
            break
    if header_row_idx is None:
        sys.exit("rbi_dla.xlsx: cannot find header row")

    # column indices (0-based, col A is index 0)
    # B=1 Sr.No, C=2 Entity Name, D=3 Website of RE, E=4 Entity Type,
    # F=5 Name of DLA, G=6 Owner, H=7 Available on, I=8 Link to DLA ...
    COL_SRNO = 1
    COL_ENTITY = 2
    COL_DLA = 5
    COL_LINK = 8

    # header repeat words to drop
    HEADER_WORDS = {"entity type", "sr. no", "name of the dla", "entity name",
                    "available on", "link to dla"}

    seen: set[tuple] = set()
    out_rows: list[dict] = []
    last_entity = ""

    for row in rows[header_row_idx + 1:]:
        srno = _clean(row[COL_SRNO])
        entity = _clean(row[COL_ENTITY])
        dla = _clean(row[COL_DLA])
        link = _clean(row[COL_LINK])

        # skip blank rows
        if not srno and not dla:
            continue

        # skip repeat-header rows
        if dla.lower() in HEADER_WORDS or srno.lower() in HEADER_WORDS:
            continue

        # carry down entity name (merged cells)
        if entity:
            last_entity = entity
        regulated_entity = last_entity

        if not dla:
            continue

        website = _extract_website(link)
        key = (dla.lower(), regulated_entity.lower(), website.lower())
        if key in seen:
            continue
        seen.add(key)
        out_rows.append({
            "dla_name": dla,
            "regulated_entity": regulated_entity,
            "website": website,
            "list_date": list_date,
        })

    out_path = OUT / "rbi_dla.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["dla_name", "regulated_entity", "website", "list_date"])
        w.writeheader()
        w.writerows(out_rows)

    distinct_apps = len({r["dla_name"].lower() for r in out_rows})
    print(f"rbi_dla.csv: {len(out_rows)} rows, {distinct_apps} distinct DLA names")
    return len(out_rows)


# ---------------------------------------------------------------------------
# STEP 2 — rbi_nbfc.csv
# ---------------------------------------------------------------------------
_FORMERLY_RE = re.compile(
    r"^(.+?)\s*\((?:formerly(?:\s+known\s+as)?:?\s*|Formerly(?:\s+known\s+as)?:?\s*|formerly:?\s*)(.+?)\)\s*$",
    re.I,
)


def _split_formerly(name: str) -> tuple[str, str]:
    """Split 'X (Formerly: Y)' -> (X, Y). Returns (name, '') if no match."""
    m = _FORMERLY_RE.match(name)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return name, ""


def build_rbi_nbfc() -> int:
    source_url = (
        "https://rbidocs.rbi.org.in/rdocs/content/DOCs/"
        "List_of_NBFCs_and_ARCs_registered_with_the_RBI.XLSX"
    )
    list_date = "2026-09-30"

    wb = openpyxl.load_workbook(RAW / "rbi_nbfc.xlsx", data_only=True)
    ws = wb["List of NBFCs"]

    # find header row
    rows = list(ws.iter_rows(values_only=True))
    header_idx = None
    for i, row in enumerate(rows):
        if _clean(row[0]).lower().startswith("sl. no"):
            header_idx = i
            break
    if header_idx is None:
        sys.exit("rbi_nbfc.xlsx: cannot find header row")

    # col indices (0-based)
    # A=0 Sl.No, B=1 NBFC Name, C=2 Regional Office, D=3 CoR holding, E=4 Classification,
    # F=5 CIN, G=6 Layer, H=7 Address, I=8 Email
    COL_SLNO = 0
    COL_NAME = 1
    COL_RO = 2
    COL_CLASS = 4
    COL_CIN = 5

    out_rows = []
    formerly_count = 0
    for row in rows[header_idx + 1:]:
        slno = _clean(row[COL_SLNO])
        # only keep rows whose Sl. No. is a whole number
        if not re.fullmatch(r"\d+", slno):
            continue

        name_raw = _clean(row[COL_NAME])
        if not name_raw:
            continue

        nbfc_name, former_name = _split_formerly(name_raw)
        if former_name:
            formerly_count += 1

        cin = _clean(row[COL_CIN])
        regional_office = _clean(row[COL_RO])
        classification = _clean(row[COL_CLASS])

        out_rows.append({
            "nbfc_name": nbfc_name,
            "former_name": former_name,
            "cin": cin,
            "regional_office": regional_office,
            "classification": classification,
            "list_date": list_date,
            "source_url": source_url,
        })

    out_path = OUT / "rbi_nbfc.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["nbfc_name", "former_name", "cin", "regional_office",
                        "classification", "list_date", "source_url"],
        )
        w.writeheader()
        w.writerows(out_rows)

    print(f"rbi_nbfc.csv: {len(out_rows)} rows, {formerly_count} with a former_name")
    return len(out_rows)


# ---------------------------------------------------------------------------
# STEP 3 — watch_list.csv (cancelled CoR)
# ---------------------------------------------------------------------------
_NOTE_PARENS_RE = re.compile(
    r"\s*[\(-]?\s*(Cancelled(?:\s+Vide\s+.+)?|formerly\s.+|Name\s+as\s+per\s+MCA.+|Cor\s+Cancelled\s+Vide\s+.+)\s*\)?\s*$",
    re.I,
)
_COR_DASH_RE = re.compile(r"^(.+?)\s*-\s*Cor\s+Cancelled\s+Vide\s+(.+)$", re.I)
_PAREN_NOTE_RE = re.compile(r"^(.*?)\s*\((.+)\)\s*$", re.S)


def _extract_name_note(raw: str) -> tuple[str, str]:
    """
    Split raw cancelled NBFC name into (name, note).
    Examples:
      "Alok Auto Credit Pvt. Ltd. (Cancelled Vide RD's Order Dated August 10, 2018)"
        -> ("Alok Auto Credit Pvt. Ltd.", "Cancelled Vide RD's Order Dated August 10, 2018")
      "Some Ltd-Cor Cancelled Vide RD's Order..."
        -> ("Some Ltd", "Cor Cancelled Vide RD's Order...")
      "Alfa Vision Overseas(I) Ltd.(Cancelled)"
        -> ("Alfa Vision Overseas(I) Ltd.", "Cancelled")
      Names with (I), (P), (India) etc in the middle -> keep in name
    """
    # strip leading whitespace / newlines
    raw = re.sub(r"^[\s\n]+", "", raw).strip()

    # dash-based "Cor Cancelled"
    m = _COR_DASH_RE.match(raw)
    if m:
        return m.group(1).strip(), ("Cor Cancelled Vide " + m.group(2)).strip()

    # parenthetical at end
    m = _PAREN_NOTE_RE.match(raw)
    if m:
        inside = m.group(2).strip()
        # skip short abbreviations like (I), (P), (India) etc that are part of the name
        ABBREVS = {"i", "p", "pvt", "ltd", "india", "s", "ii", "iii"}
        if inside.lower() in ABBREVS or (len(inside) <= 3 and inside.replace(".", "").isalpha()):
            return raw, ""
        # check if parenthetical looks like a note (contains Cancelled, Vide, Order, MCA, Formerly etc)
        NOTE_WORDS = re.compile(r"\b(cancelled|vide|order|mca|formerly|name\s+as\s+per|cor\s+cancel|restored)\b", re.I)
        if NOTE_WORDS.search(inside):
            return m.group(1).strip(), inside
        # another common pattern: last parens is a note if name ends with Ltd./Ltd etc already
        name_part = m.group(1).strip()
        if re.search(r"\b(ltd|limited|pvt|private|corp|corporation|co)\b\.?\s*$", name_part, re.I):
            # already a complete company name: treat the parens content as note
            return name_part, inside
        # otherwise the parens is part of the name (e.g. "Overseas(I) Ltd.")
        return raw, ""

    return raw, ""


def _make_key(name: str) -> str:
    """Lower, keep only letters+digits, remove pvt/private/ltd/limited/p/the."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    STOPS = {"pvt", "private", "ltd", "limited", "p", "the"}
    tokens = [t for t in s.split() if t and t not in STOPS]
    return "".join(tokens)


def build_watch_list(nbfc_csv_path: Path) -> int:
    source_url = (
        "https://rbidocs.rbi.org.in/rdocs/content/DOCs/"
        "List_of_NBFCs_and_ARCs_whose_CoR_has_been_cancelled_by_the_RBI.XLSX"
    )
    source_date = "2026-09-30"
    list_name = "RBI: registration cancelled"

    # build key set from registered NBFCs
    registered_keys: set[str] = set()
    with open(nbfc_csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            registered_keys.add(_make_key(row["nbfc_name"]))
            if row["former_name"]:
                registered_keys.add(_make_key(row["former_name"]))
    # remove empty key
    registered_keys.discard("")

    wb = openpyxl.load_workbook(RAW / "rbi_cancelled_nbfc.xlsx", data_only=True)

    # collect Record sheet names -> keys to exclude (CoR restored)
    record_keys: set[str] = set()
    ws_rec = wb["Record"]
    for row in ws_rec.iter_rows(values_only=True):
        name = _clean(row[2])  # col C = NBFC Name
        if name and name.lower() not in ("nbfc name", ""):
            record_keys.add(_make_key(name))
    record_keys.discard("")

    ws = wb["Cancelled List"]
    rows = list(ws.iter_rows(values_only=True))

    # find header
    header_idx = None
    for i, row in enumerate(rows):
        if _clean(row[0]).lower().startswith("sl. no"):
            header_idx = i
            break
    if header_idx is None:
        sys.exit("rbi_cancelled_nbfc.xlsx: cannot find header row")

    COL_SLNO = 0
    COL_NAME = 1

    out_rows = []
    exc_a = exc_b = exc_c = 0
    exc_b_names = []

    for row in rows[header_idx + 1:]:
        slno = _clean(row[COL_SLNO])
        if not re.fullmatch(r"\d+", slno):
            continue

        raw_name = _clean(row[COL_NAME])
        if not raw_name:
            continue

        name, note = _extract_name_note(raw_name)
        key = _make_key(name)

        # (a) in Record sheet
        if key in record_keys:
            exc_a += 1
            continue

        # (b) key matches a registered NBFC
        if key in registered_keys:
            exc_b += 1
            exc_b_names.append(name)
            continue

        # (c) key too short
        if len(key) < 4:
            exc_c += 1
            continue

        out_rows.append({
            "name": name,
            "website": "",
            "list_name": list_name,
            "source_type": "official",
            "source_url": source_url,
            "source_date": source_date,
            "note": note,
        })

    out_path = OUT / "watch_list.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["name", "website", "list_name", "source_type",
                         "source_url", "source_date", "note"],
        )
        w.writeheader()
        w.writerows(out_rows)

    print(f"watch_list.csv: {len(out_rows)} rows")
    print(f"  excluded: (a) Record sheet = {exc_a}, (b) registered today = {exc_b}, (c) key too short = {exc_c}")
    print(f"  (b) names excluded because still registered: {exc_b_names[:10]} ...")
    return len(out_rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # DLA list date — download date, no date shown on the RBI page
    DLA_LIST_DATE = "2026-11-14"

    print("=== Building rbi_dla.csv ===")
    build_rbi_dla(DLA_LIST_DATE)

    print("\n=== Building rbi_nbfc.csv ===")
    build_rbi_nbfc()

    print("\n=== Building watch_list.csv ===")
    build_watch_list(OUT / "rbi_nbfc.csv")

    print("\nDone.")
