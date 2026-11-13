"""RBI directory match (task C1, mentor feedback D37). Never says "safe", "illegal" or "fake"; always gives the list date.

Compares against a local copy of RBI's public directory of digital lending apps:
api/data/rbi_dla.csv (columns dla_name, regulated_entity, website, list_date; website may be empty).
No live call to RBI. Matching:
- name: whole-name similarity (RapidFuzz ratio) of the app / lender name read from the ad against each
  app name AND each regulated entity, after removing generic words (loan, app, pvt, ltd...); no partial
  or word-order matching (see _score). >= lender_found_score FOUND, >= lender_similar_score SIMILAR,
  else NOT_FOUND (thresholds in config).
- website: a link in the SMS / ad whose domain equals a listed app's website -> FOUND.
  A FOUND name with a link to a DIFFERENT domain than that app's website -> SIMILAR (a possible clone).
If the directory file is empty, or nothing was read to check, match is None ("not checked", D26).
"""
import csv
import logging
import re
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz, process, utils

from api.core import config

log = logging.getLogger("lender")

GENERIC = {"loan", "loans", "app", "apps", "application", "instant", "online", "personal", "india",
           "pvt", "private", "ltd", "limited", "the", "official"}
_DOMAIN = re.compile(r"(?:https?://)?(?:www\.)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:[/:?#][^\s]*)?", re.I)
_PLAY_ID = re.compile(r"[?&]id=([a-z0-9_.]+)", re.I)
_TWO_PART_TLDS = {"co.in", "org.in", "net.in", "gov.in", "ac.in", "firm.in", "gen.in", "ind.in", "co.uk"}


def _compact(name: str) -> str:
    """'Kredit Bee App' -> 'kreditbee': lower case, generic words and spaces removed."""
    words = [w for w in utils.default_process(name).split() if w not in GENERIC]
    return "".join(words)


def _score(query: str, candidate: str) -> float:
    """Whole-name similarity of the cleaned names, 0-100.

    With RBI's real list (1,222 apps) a partial or word-order score (WRatio) said "found" for invented
    names ("Kanak Credit" -> "Cred", "Tez Kanak" -> an app named "NA"), so only whole names count:
    the same cleaned name = 100; a name under 4 letters counts only when it is exactly the same;
    otherwise plain fuzz.ratio of the two cleaned names.
    """
    a, b = _compact(query or ""), _compact(candidate or "")
    if not a or not b:
        return 0.0
    if a == b:
        return 100.0
    if min(len(a), len(b)) < 4:
        return 0.0
    return fuzz.ratio(a, b)


def _site(value: str | None) -> str | None:
    """A website or Play Store link -> 'kreditbee.in' (registered domain) or 'play:com.kreditbee.app'."""
    if not value:
        return None
    play = _PLAY_ID.search(value)
    if play and "play.google" in value.lower():
        return "play:" + play.group(1).lower()
    m = _DOMAIN.search(value.strip().lower())
    if not m:
        return None
    parts = m.group(1).split(".")
    keep = 3 if ".".join(parts[-2:]) in _TWO_PART_TLDS and len(parts) >= 3 else 2
    return ".".join(parts[-keep:])


def sites_in(text: str | None) -> list[str]:
    """Every website / Play Store link written in a message."""
    if not text:
        return []
    found = []
    for token in re.findall(r"\S+", text):
        if "." in token and not re.fullmatch(r"[\d.,₹]+", token):
            site = _site(token)
            if site and site not in found and not site.endswith((".jpg", ".png")):
                found.append(site)
    return found


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> tuple[list[dict], str | None]:
    rows, dates = [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            name = (r.get("dla_name") or "").strip()
            if not name:
                continue
            rows.append({"dla_name": name, "regulated_entity": (r.get("regulated_entity") or "").strip(),
                         "site": _site(r.get("website")), "list_date": (r.get("list_date") or "").strip()})
            if rows[-1]["list_date"]:
                dates.append(rows[-1]["list_date"])
    return rows, (max(dates) if dates else None)


def directory() -> tuple[list[dict], str | None]:
    """(rows, list date). Re-read automatically when the CSV file changes."""
    path = Path(config.settings.rbi_dla_path)
    if not path.is_file():
        return [], None
    return _load(str(path), path.stat().st_mtime)


# ---- C3 / D51: RBI's NBFC list and the cancelled-registration list (built by scripts/build_ledger.py) ----
@lru_cache(maxsize=8)
def _read_csv(path: str, mtime: float) -> tuple[dict, ...]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return tuple(csv.DictReader(f))


def _csv_rows(path_setting: str) -> tuple[dict, ...]:
    """Rows of a list file; a missing file means "not checked" (empty), never an error."""
    path = Path(path_setting)
    if not path.is_file():
        return ()
    return _read_csv(str(path), path.stat().st_mtime)


def _exact_key(name: str) -> str:
    """Key for the cancelled list: the cleaned name, also without a lone "P" ("Rajmandir Estates (P) Ltd")."""
    words = [w for w in utils.default_process(name or "").split() if w not in GENERIC and w != "p"]
    return "".join(words)


@lru_cache(maxsize=4)
def _nbfc_index(path: str, mtime: float) -> tuple[dict[str, dict], list[str]]:
    """cleaned name (current or former) -> {"name", "list_date"}; plus the keys for fuzzy lookup."""
    index: dict[str, dict] = {}
    for r in _read_csv(path, mtime):
        entry = {"name": (r.get("nbfc_name") or "").strip(), "list_date": (r.get("list_date") or "").strip() or None}
        for n in (r.get("nbfc_name"), r.get("former_name")):
            k = _compact(n or "")
            if k and k not in index:
                index[k] = entry
    return index, list(index)


@lru_cache(maxsize=4)
def _watch_index(path: str, mtime: float) -> dict[str, dict]:
    """cleaned name -> the list row. An "official" source wins over a "news" one for the same name."""
    index: dict[str, dict] = {}
    for r in _read_csv(path, mtime):
        k = _exact_key(r.get("name") or "")
        if len(k) < 5:
            continue
        if k not in index or (r.get("source_type") == "official" and index[k].get("source_type") != "official"):
            index[k] = r
    return index


def _nbfc_for(names: list[str]) -> dict | None:
    """C3: is one of these names (the lender read from the ad, or the lender behind a FOUND app) an
    NBFC registered with RBI? Whole-name match like the app list: exact, or ratio >= lender_found_score."""
    path = Path(config.settings.rbi_nbfc_path)
    if not path.is_file():
        return None
    index, keys = _nbfc_index(str(path), path.stat().st_mtime)
    for name in names:
        k = _compact(name or "")
        if not k:
            continue
        if k in index:
            return dict(index[k])
        if len(k) >= 4:
            hit = process.extractOne(k, keys, scorer=fuzz.ratio, score_cutoff=config.settings.lender_found_score)
            if hit:
                return dict(index[hit[0]])
    return None


def _warning_for(name: str | None) -> dict | None:
    """D51: the name read from the ad is on RBI's cancelled-registration list. EXACT cleaned name only,
    never fuzzy: a similar-sounding lender must never be told off. Worded as a sourced fact."""
    path = Path(config.settings.watch_list_path)
    k = _exact_key(name or "")
    if len(k) < 5 or not path.is_file():
        return None
    row = _watch_index(str(path), path.stat().st_mtime).get(k)
    if not row:
        return None
    return {"list": row.get("list_name") or "", "name": (row.get("name") or "").strip(),
            "source_type": row.get("source_type") or "", "date": row.get("source_date") or None,
            "source": row.get("source_url") or ""}


def _closest(row: dict) -> str:
    return f"{row['dla_name']} ({row['regulated_entity']})" if row["regulated_entity"] else row["dla_name"]


def match_lender(name: str | None, text: str | None = None) -> dict:
    """-> CheckResult.lender: {"name_read", "match", "score", "closest", "list_date", "nbfc", "warning"}.

    nbfc and warning (D51) are optional extras, null unless found; match keeps its meaning.
    """
    result = _match_app(name, text)
    best_entity = result.pop("_entity", None)
    result["warning"] = None if result["match"] == "FOUND" else _warning_for(result["name_read"])
    names = [n for n in (result["name_read"], best_entity if result["match"] == "FOUND" else None) if n]
    result["nbfc"] = None if result["warning"] else _nbfc_for(names)
    return result


def _match_app(name: str | None, text: str | None = None) -> dict:
    """C1: the RBI directory of digital lending apps."""
    rows, list_date = directory()
    name = (name or "").strip() or None
    sites = sites_in(text)
    result = {"name_read": name, "match": None, "score": None, "closest": None, "list_date": list_date}
    if not rows or (not name and not sites):
        return result                                   # nothing to check against, or nothing read

    s = config.settings
    by_site = next((r for r in rows if r["site"] and r["site"] in sites), None)
    if by_site:                                         # the link itself is a listed app's website
        result.update(match="FOUND", score=100.0, closest=_closest(by_site), _entity=by_site["regulated_entity"])
        return result

    best, best_score = None, 0.0
    if name:
        for r in rows:
            sc = max(_score(name, r["dla_name"]), _score(name, r["regulated_entity"]))
            if sc > best_score:
                best, best_score = r, sc
    score = round(best_score, 1)
    if best is not None and best_score >= s.lender_found_score:
        if sites and best["site"] and best["site"] not in sites:
            # the name matches a listed app, but the link goes somewhere else: possible clone
            result.update(match="SIMILAR", score=score, closest=_closest(best))
        else:
            result.update(match="FOUND", score=score, closest=_closest(best), _entity=best["regulated_entity"])
    elif best is not None and best_score >= s.lender_similar_score:
        result.update(match="SIMILAR", score=score, closest=_closest(best))
    else:
        result.update(match="NOT_FOUND", score=score, closest=None)
    log.info("lender: %s -> %s (score %s)", name or sites, result["match"], result["score"])
    return result
