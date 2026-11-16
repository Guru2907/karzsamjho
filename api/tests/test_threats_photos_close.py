"""D60: threat type, evidence photos, the PDF in parts, closing a case. Synthetic data only; no internet."""
import hashlib
import io
import json

import pytest
from PIL import Image

from api.core import db, evidence, harass
from api.main import event_hash


@pytest.fixture(autouse=True)
def text_rules(monkeypatch):
    """A stand-in for the text labelling (no AI in tests): "warna" -> H2, after 19:00 -> H1."""
    def label(event, calls_that_day):
        rules = set()
        if event["at"][11:13] >= "19" or event["at"][11:13] < "08":
            rules.add("H1")
        if "warna" in (event.get("text") or "").lower():
            rules.add("H2")
        return sorted(rules)
    monkeypatch.setattr(harass, "label", label)


def new_case(client):
    return client.post("/api/cases", json={"borrower_name": "Raju", "lender_name": "Kulhad Capital Ltd."}).json()


def form(text="Legal Threats", threat_type="legal", at="2026-11-17T03:27:00+05:30"):
    return {"at": at, "channel": "whatsapp", "contacted": "neighbour", "text": text, "threat_type": threat_type}


def photo(color=(200, 40, 40), size=(2400, 1800), gps=True) -> bytes:
    """A synthetic JPEG; with gps=True it carries EXIF location data like a phone photo."""
    im = Image.new("RGB", size, color)
    out = io.BytesIO()
    exif = Image.Exif()
    if gps:
        exif[0x8825] = {1: "N", 2: (19.0, 4.0, 30.0), 3: "E", 4: (72.0, 52.0, 0.0)}   # GPSInfo
        exif[0x0110] = "Phone X"                                                     # Model
    im.save(out, "JPEG", exif=exif)
    return out.getvalue()


def post_photos(client, cid, files, **kw):
    return client.post(f"/api/cases/{cid}/events", data=form(**kw),
                       files=[("photos", (f"p{i}.jpg", b, "image/jpeg")) for i, b in enumerate(files)])


# ---------------------------------------------------------------- 1. threat type
def test_type_adds_its_rule_and_keeps_the_text_rules(client):
    cid = new_case(client)["id"]
    ev = client.post(f"/api/cases/{cid}/events", json=form(text="Paisa do warna", threat_type="legal")).json()
    assert ev["threat_type"] == "legal" and ev["rules"] == ["H1", "H2", "H5"]   # H1 time, H2 words, H5 type


@pytest.mark.parametrize("kind, rule", [("death", "H2"), ("verbal", "H2"), ("legal", "H5"), ("shaming", "H4"),
                                        ("visit", None), ("other", None)])
def test_each_type_and_its_rule(kind, rule):
    assert harass.type_rules(kind) == ({rule} if rule else set())
    assert kind in harass.THREAT_TYPES


def test_unknown_type_is_refused_in_hindi(client):
    cid = new_case(client)["id"]
    r = client.post(f"/api/cases/{cid}/events", json=form(threat_type="alien"))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "BAD_TYPE"


def test_old_events_keep_exactly_their_old_hash():
    """An event with no type and no photos hashes exactly as before D60, so old cases still verify."""
    ev = {"at": "2026-11-13T21:40:00+05:30", "channel": "call", "contacted": "borrower", "text": "x",
          "rules": ["H1"], "threat_type": None, "photos": []}
    old = {k: ev[k] for k in ("at", "channel", "contacted", "text", "rules")}
    body = json.dumps(old, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert event_hash("0" * 64, ev) == hashlib.sha256(("0" * 64 + body).encode()).hexdigest()
    assert evidence.event_hash("0" * 64, ev) == event_hash("0" * 64, ev)


def test_type_is_covered_by_the_hash(client):
    cid = new_case(client)["id"]
    client.post(f"/api/cases/{cid}/events", json=form(threat_type="legal"))
    with db._db() as conn:
        conn.execute("UPDATE events SET threat_type = 'other'")
        conn.commit()
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": False}


# ---------------------------------------------------------------- 2. photos
def test_photos_are_stored_cleaned_and_listed(client):
    cid = new_case(client)["id"]
    r = post_photos(client, cid, [photo(), photo((20, 20, 200))])
    assert r.status_code == 200
    ev = r.json()
    assert len(ev["photos"]) == 2
    got = client.get(f"/api/cases/{cid}/photos/{ev['photos'][0]['id']}.jpg")
    assert got.status_code == 200 and got.headers["content-type"] == "image/jpeg"
    assert hashlib.sha256(got.content).hexdigest() == ev["photos"][0]["sha256"]
    with Image.open(io.BytesIO(got.content)) as im:
        assert max(im.size) == evidence.MAX_PHOTO_SIDE                        # 2400 px -> 1600 px
        assert 0x8825 not in im.getexif() and 0x0110 not in im.getexif()    # no GPS, no phone model
    case = client.get(f"/api/cases/{cid}").json()
    assert [p["id"] for p in case["events"][0]["photos"]] == [p["id"] for p in ev["photos"]]
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": True}


def test_a_photo_only_opens_through_its_own_case(client):
    a, b = new_case(client)["id"], new_case(client)["id"]
    pid = post_photos(client, a, [photo()]).json()["photos"][0]["id"]
    assert client.get(f"/api/cases/{b}/photos/{pid}.jpg").status_code == 404


def test_swapping_or_removing_a_photo_breaks_verify(client):
    cid = new_case(client)["id"]
    post_photos(client, cid, [photo(), photo((0, 120, 0))])
    with db._db() as conn:                                   # swap in another picture, fingerprint too
        new = evidence.clean_photo(photo((0, 0, 0)))
        conn.execute("UPDATE photos SET data = ?, sha256 = ? WHERE position = 0", (new, hashlib.sha256(new).hexdigest()))
        conn.commit()
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": False}


def test_changing_a_photo_but_not_its_fingerprint_also_breaks_verify(client):
    cid = new_case(client)["id"]
    post_photos(client, cid, [photo()])
    with db._db() as conn:
        conn.execute("UPDATE photos SET data = ?", (evidence.clean_photo(photo((1, 2, 3))),))
        conn.commit()
    assert client.get(f"/api/cases/{cid}/verify").json() == {"ok": False}


def test_more_than_3_photos_or_a_non_picture_is_refused(client):
    cid = new_case(client)["id"]
    assert post_photos(client, cid, [photo()] * 4).json()["detail"]["code"] == "TOO_MANY_PHOTOS"
    assert post_photos(client, cid, [b"not a picture"]).json()["detail"]["code"] == "BAD_PHOTO"
    assert client.get(f"/api/cases/{cid}").json()["events"] == []        # nothing half-stored


def test_json_without_photos_still_works_for_the_bot(client):
    cid = new_case(client)["id"]
    r = client.post(f"/api/cases/{cid}/events", json={"at": "2026-11-17T10:00:00+05:30", "channel": "telegram",
                                                      "contacted": "borrower", "text": "Kal aayenge"})
    assert r.status_code == 200 and r.json()["threat_type"] is None and r.json()["photos"] == []


# ---------------------------------------------------------------- 3. the PDF in parts
def _pages(pdf: bytes) -> list[str]:
    """The text blocks of an uncompressed PDF, one per page (in page order)."""
    raw = pdf.decode("latin-1").replace("\\(", "(").replace("\\)", ")")
    return [part.split("endstream")[0] for part in raw.split("stream\n")[1:] if "BT" in part.split("endstream")[0]]


def test_complaint_always_starts_on_its_own_page_and_photos_after(client):
    cid = new_case(client)["id"]
    ev = post_photos(client, cid, [photo(), photo((0, 0, 200))], text="Paisa do warna").json()
    case = client.get(f"/api/cases/{cid}").json()
    pics = {p["id"]: db.get_photo(cid, p["id"]) for p in ev["photos"]}
    pages = _pages(evidence.build_pdf(case, compress=False, photos=pics))
    where = {h: next(i for i, t in enumerate(pages) if h in t)
             for h in ("Rules broken", "Record integrity", "Part 2: Complaint", "Complaint draft", "Part 3: Photos")}
    assert where["Rules broken"] == where["Record integrity"] == 0                 # all evidence on page 1
    assert where["Part 2: Complaint"] == where["Complaint draft"] == 1             # the letter: a new page
    assert where["Part 3: Photos"] == 2                                            # photos: another new page
    assert "[Photo 1, 2, see Part 3]" in pages[0] and "Legal or police" in pages[0]   # photo refs + Type column


def test_no_photos_means_no_part_3():
    case = {"id": "case_x", "borrower_name": "Raju", "lender_name": "QuickCash", "opened_at": "2026-11-17T10:00:00+05:30",
            "events": []}
    text = evidence.build_pdf(case, compress=False).decode("latin-1")
    assert "Part 2: Complaint" in text and "Part 3: Photos" not in text


def test_lender_ending_with_a_full_stop_is_not_doubled():
    case = {"lender_name": "Kulhad Capital Ltd.", "borrower_name": "Raju", "events": []}
    letter = " ".join(evidence.complaint_draft(case, {}))
    assert "Ltd.." not in letter and "Kulhad Capital Ltd" in letter


# ---------------------------------------------------------------- 4. closing a case
def test_close_a_case(client):
    case = new_case(client)
    client.post(f"/api/cases/{case['id']}/events", json=form())
    r = client.post(f"/api/cases/{case['id']}/close", json={"reason": "complaint_filed", "note": "Filed on Sachet"})
    closed = r.json()
    assert r.status_code == 200 and closed["closed_at"] and closed["close_reason"] == "complaint_filed"
    assert closed["close_note"] == "Filed on Sachet" and closed["day"] == 1
    again = client.post(f"/api/cases/{case['id']}/close", json={"reason": "resolved"})
    assert again.status_code == 409 and again.json()["detail"]["code"] == "ALREADY_CLOSED"
    blocked = client.post(f"/api/cases/{case['id']}/events", json=form())
    assert blocked.status_code == 409 and blocked.json()["detail"]["code"] == "CASE_CLOSED"
    # still readable: the code, the PDF and verify keep working
    assert client.get(f"/api/cases/code/{case['code']}").json()["closed_at"] == closed["closed_at"]
    assert client.get(f"/api/cases/{case['id']}/verify").json() == {"ok": True}
    pdf = client.get(f"/api/cases/{case['id']}/evidence.pdf")
    assert pdf.status_code == 200


def test_closed_status_line_in_the_pdf():
    case = {"id": "case_x", "borrower_name": "Raju", "lender_name": "QuickCash", "opened_at": "2026-11-15T10:00:00+05:30",
            "closed_at": "2026-11-17T09:00:00+05:30", "close_reason": "repaid", "events": []}
    text = evidence.build_pdf(case, compress=False).decode("latin-1")
    assert "Status: Closed on 17 Nov 2026" in text and "Loan repaid" in text
    open_case = {**case, "closed_at": None}
    assert "Status: Open" in evidence.build_pdf(open_case, compress=False).decode("latin-1")


def test_day_counter_stops_when_closed(client):
    case = new_case(client)
    with db._db() as conn:
        conn.execute("UPDATE cases SET opened_at = '2026-11-01T10:00:00+05:30' WHERE id = ?", (case["id"],))
        conn.commit()
    client.post(f"/api/cases/{case['id']}/close", json={"reason": "stopped"})
    with db._db() as conn:
        conn.execute("UPDATE cases SET closed_at = '2026-11-04T10:00:00+05:30' WHERE id = ?", (case["id"],))
        conn.commit()
    assert client.get(f"/api/cases/{case['id']}").json()["day"] == 4


def test_bad_reason_and_missing_case(client):
    cid = new_case(client)["id"]
    assert client.post(f"/api/cases/{cid}/close", json={"reason": "bored"}).status_code == 422
    assert client.post("/api/cases/case_nope/close", json={"reason": "resolved"}).status_code == 404


def test_bot_memory_says_closed(client):
    key = "ef" * 20
    case = client.post("/api/cases", json={"borrower_name": "Raju", "lender_name": "Q", "telegram_chat": key}).json()
    client.post(f"/api/cases/{case['id']}/close", json={"reason": "resolved"})
    assert client.get(f"/api/telegram/{key}").json()["closed"] is True
