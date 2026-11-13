"""Run the demo pack (G1, G8, G2; D52) through the REAL API and compare with the hand-worked answers.

    scripts\\run_api.bat                                   # in another window (port 8000)
    python scripts/run_demo_pack.py                       # or: --api http://127.0.0.1:8077 --pace 15

For every image (api/data/offers/demo_pack.json) and SMS (api/data/offers/sms_demo.json): POST /api/checks and
compare in_hand, repay_total, tenure_days, extra, verdict, lender flag and next_step with "expected".
For the harassment samples (api/data/harassment/samples.json): POST /api/cases, each sample to
/api/cases/{id}/events, compare the rules, then GET evidence.pdf (Aadhaar masked?) and /verify.

K = numbers shown as VERIFIED on the card that are WRONG (the K = 0 rule). A number shown as "couldn't verify"
where we expected a value is a MISS, not K. This script never changes an expected answer or any code:
a mismatch is a finding for the team.
Needs: httpx (already in api/requirements.txt). No keys are read or printed here; the API uses its own .env.
"""
import argparse
import base64
import json
import re
import sys
import time
import zlib
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OFFERS = ROOT / "api" / "data" / "offers"
HARASS = ROOT / "api" / "data" / "harassment" / "samples.json"
NUMBERS = ("in_hand", "repay_total", "tenure_days", "extra")


def flag(lender: dict | None) -> str | None:
    """FOUND / SIMILAR / NOT_FOUND / WARNING (the brief's label) from CheckResult.lender."""
    if not lender:
        return None
    return "WARNING" if lender.get("warning") else lender.get("match")


def compare(exp: dict, got: dict) -> tuple[list[str], int, int]:
    """-> (problems, K wrong-but-verified numbers, misses)."""
    problems, k, miss = [], 0, 0
    nums = got.get("numbers") or {}
    for key in NUMBERS:
        item = nums.get(key) or {}
        shown = item.get("value") if item.get("status") != "unverified" else None
        want = exp.get(key)
        if shown is None and want is None:
            continue
        if shown is None:
            miss += 1
            problems.append(f"{key}: couldn't verify, expected {want}")
        elif want is None or abs(float(shown) - float(want)) > 1:
            k += 1
            problems.append(f"{key}: shown {shown} ({item.get('status')}), expected {want}  <- K")
    if got.get("verdict") != exp["verdict"]:
        problems.append(f"verdict {got.get('verdict')}, expected {exp['verdict']}")
    if flag(got.get("lender")) != exp["lender_flag"]:
        problems.append(f"lender {flag(got.get('lender'))}, expected {exp['lender_flag']}")
    if bool((got.get("lender") or {}).get("nbfc")) != bool(exp.get("nbfc")):
        problems.append(f"nbfc {'shown' if (got.get('lender') or {}).get('nbfc') else 'missing'}, expected "
                        f"{'shown' if exp.get('nbfc') else 'none'}")
    step = (got.get("next_step") or {}).get("code")
    if step != exp["next_step"]:
        problems.append(f"next_step {step}, expected {exp['next_step']}")
    warned = str(got.get("speech_text_hi") or "")[:12].lower()
    said_warning = any(w in warned for w in ("savdhaan", "সাবধান", "सावधान"))
    if bool(exp.get("pay_first")) != said_warning:
        problems.append(f"pay-first warning {'spoken' if said_warning else 'not spoken'}, expected "
                        f"{'spoken' if exp.get('pay_first') else 'none'}")
    if exp.get("second_read") and not (got.get("engines") or {}).get("second_read"):
        problems.append("second reading expected, none recorded")
    return problems, k, miss


def show(value):
    return "-" if value is None else (f"{value:g}" if isinstance(value, (int, float)) else str(value))


def row(rid, exp, got, problems, seconds) -> str:
    nums = got.get("numbers") or {}
    def g(key):
        item = nums.get(key) or {}
        return "?" if item.get("status") == "unverified" else show(item.get("value"))
    cells = [rid]
    for key in NUMBERS:
        cells.append(f"{show(exp.get(key))} / {g(key)}")
    cells += [f"{exp['verdict']} / {got.get('verdict')}", f"{exp['lender_flag']} / {flag(got.get('lender'))}",
              f"{exp['next_step']} / {(got.get('next_step') or {}).get('code')}",
              "OK" if not problems else "MISMATCH", f"{seconds:.1f}"]
    return "| " + " | ".join(cells) + " |"


def post_check(client, api, *, image=None, text=None, lang="hi"):
    start = time.perf_counter()
    if image is not None:
        r = client.post(f"{api}/api/checks", files={"image": (image.name, image.read_bytes(), "image/png")},
                        data={"lang": lang, "source": "demo-pack"})
    else:
        r = client.post(f"{api}/api/checks", json={"text": text, "lang": lang, "source": "demo-pack"})
    seconds = time.perf_counter() - start
    try:
        body = r.json()
    except ValueError:
        body = {}
    if r.status_code != 200:
        body = {"_error": f"HTTP {r.status_code}: {json.dumps(body, ensure_ascii=False)[:160]}"}
    return body, seconds


def pdf_text(data: bytes) -> str:
    """Text drawn in a ReportLab PDF (ASCII85 + Flate streams), for the masking check."""
    out = []
    for raw in re.findall(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = raw.strip()
        try:
            raw = zlib.decompress(base64.a85decode(raw[:-2] if raw.endswith(b"~>") else raw))
        except Exception:
            try:
                raw = zlib.decompress(raw)
            except Exception:
                pass
        out += [t.decode("latin-1") for t in re.findall(rb"\(((?:[^()\\]|\\.)*)\)\s*Tj", raw)]
    return " ".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--api", default="http://127.0.0.1:8000")
    ap.add_argument("--pace", type=float, default=12.0, help="seconds between photos (Groq: about 3 photos a minute)")
    ap.add_argument("--only", choices=("images", "sms", "harassment"), help="run one part only")
    args = ap.parse_args()
    api = args.api.rstrip("/")
    head = ("| id | in_hand exp / got | repay exp / got | days exp / got | extra exp / got | verdict exp / got "
            "| lender exp / got | next step exp / got | result | sec |\n|" + "---|" * 10)
    total_k = total_miss = mismatches = 0
    findings = []

    with httpx.Client(timeout=90) as client:
        health = client.get(f"{api}/api/health").json()
        print(f"API {api}: engines " + ", ".join(f"{k} {'up' if v.get('up') else 'DOWN'}"
                                                 for k, v in (health.get("engines") or {}).items()))
        groups = []
        if args.only in (None, "images"):
            groups.append(("Images (G1)", [(it["id"], it["expected"], {"image": OFFERS / it["file"], "lang": it.get("lang", "hi")})
                                           for it in json.loads((OFFERS / "demo_pack.json").read_text(encoding="utf-8"))["items"]]))
        if args.only in (None, "sms"):
            groups.append(("SMS (G8)", [(it["id"], it["expected"], {"text": it["text"], "lang": it.get("lang", "hi")})
                                        for it in json.loads((OFFERS / "sms_demo.json").read_text(encoding="utf-8"))["items"]]))
        for title, items in groups:
            print(f"\n### {title}\n{head}")
            for n, (rid, exp, kwargs) in enumerate(items):
                if "image" in kwargs and n:
                    time.sleep(args.pace)
                got, seconds = post_check(client, api, **kwargs)
                if "_error" in got:
                    mismatches += 1
                    findings.append(f"{rid}: {got['_error']}")
                    print(f"| {rid} | {got['_error']} |" + " |" * 8)
                    continue
                problems, k, miss = compare(exp, got)
                total_k += k
                total_miss += miss
                mismatches += bool(problems)
                findings += [f"{rid}: {p}" for p in problems]
                print(row(rid, exp, got, problems, seconds))

        if args.only in (None, "harassment"):
            pack = json.loads(HARASS.read_text(encoding="utf-8"))
            print("\n### Harassment (G2)\n| id | at | expected rules | got rules | result |\n|---|---|---|---|---|")
            case = client.post(f"{api}/api/cases", json=pack["case"]).json()
            for it in pack["items"]:
                body = {k: it[k] for k in ("at", "channel", "contacted", "text")}
                ev = client.post(f"{api}/api/cases/{case['id']}/events", json=body).json()
                got_rules = sorted(ev.get("rules") or [])
                ok = got_rules == sorted(it["expected_rules"])
                mismatches += not ok
                if not ok:
                    findings.append(f"{it['id']}: rules {got_rules}, expected {it['expected_rules']}")
                print(f"| {it['id']} | {it['at'][11:16]} | {', '.join(it['expected_rules']) or 'none'} | "
                      f"{', '.join(got_rules) or 'none'} | {'OK' if ok else 'MISMATCH'} |")
            pdf = client.get(f"{api}/api/cases/{case['id']}/evidence.pdf")
            text = pdf_text(pdf.content)
            masked = "XXXX XXXX 9012" in text and "1234 5678 9012" not in text
            verify = client.get(f"{api}/api/cases/{case['id']}/verify").json()
            print(f"\nEvidence PDF: HTTP {pdf.status_code}, {len(pdf.content)} bytes, Aadhaar masked as XXXX XXXX 9012: "
                  f"{'yes' if masked else 'NO'}; /verify ok: {verify.get('ok')}")
            if not masked:
                mismatches += 1
                findings.append("evidence PDF: Aadhaar not masked as XXXX XXXX 9012")
            if verify.get("ok") is not True:
                mismatches += 1
                findings.append(f"verify: {verify}")

    print(f"\nK (numbers shown as verified that are WRONG) = {total_k}")
    print(f"Misses (expected a number, card says couldn't verify) = {total_miss}")
    print(f"Items or checks with a mismatch = {mismatches}")
    if findings:
        print("\nFindings (for the team; expected answers and code are NOT changed):")
        for f in findings:
            print(f"- {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
