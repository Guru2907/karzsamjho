# PLAN.md: the plan for the 7:30 PM review (written 13 Nov, 5:00 PM IST)

This replaces the earlier split. Decision D25 in docs/DECISIONS.md. If this file and the code disagree, trust the code and fix this file.

## Goal for the review (7:30 PM, may run to 9 PM)

1. **Photo.** A photo of a loan ad, sent in Telegram or uploaded on the web `/check` page, comes back as a card with big rupee numbers plus a Hindi voice message (MP3).
2. **Text.** A pasted SMS offer, in Telegram or on `/check`, comes back as the same card and voice.
3. **Second reading.** If the numbers read from a photo do not add up, the other reader reads the photo again. Fields the two readers disagree on are shown as "couldn't verify".

How one check flows: reader (AI) copies the written numbers -> Python checks they add up -> Python does the maths -> Python picks the verdict -> fixed Hindi sentence -> MP3.

## Skipped until after the review

Harassment log, evidence PDF, lender / RBI match, a real next step (a fixed line for now), database, cache. Results live in memory, so they are lost when the server restarts. That is fine for the review.

## Who does what

| Person | Tool | Job | Only these files |
|---|---|---|---|
| Lead | Claude Code | Calls to the AI services, reading photos and text, second reading, joining everything in the API | `api/core/fallback.py`, `api/core/extract.py`, `api/core/schemas.py`, `api/main.py`, `api/tests/test_extract.py`, `api/tests/test_pipeline.py`, `api/tests/test_smoke.py`, `docs/` |
| Claude Code teammate | Claude Code | Rupee maths, verdict, Hindi sentence + MP3, Telegram bot | `api/core/maths.py`, `api/core/verdict.py`, `api/core/speak.py`, `bot/main.py`, `api/tests/test_maths.py`, `api/tests/test_verdict.py`, `api/tests/test_speak.py` |
| PWA teammate | Antigravity | The web app: `/check` page and the Raju card | `web/src/` only |
| Data teammate | Antigravity | Printed demo ads, text offers, expected numbers, RBI list | `api/data/` only |

Nobody edits a file in another person's row. If you need a change there, ask that person.

**Getting code onto main:** pull main before each item. Push each finished item on its own, straight away (a branch and a pull request if GitHub refuses a direct push; the lead merges at once). Small and often, never one big push at 6:55.

## Order and target times (IST)

### Lead
| # | Target | Item | Task | File |
|---|---|---|---|---|
| L1 | 5:25 | `speak()`: text -> MP3 with edge-tts. First, because the teammate needs it. | A4 | `fallback.py` |
| L2 | 5:45 | `read_image()` (Qwen, then Gemini) and `read_text()` (gpt-oss-20b): timeout, temperature 0, no retry, a 429 moves on at once, token counts logged | A4, A6 | `fallback.py` |
| L3 | 6:10 | Photo -> fields, text -> fields with a regex backup, not-a-loan check | B1, B2, B7, B8 | `extract.py` |
| L4 | 6:30 | Join the parts in `POST /api/checks`; keep results in memory; serve the MP3 | A7 | `main.py`, `schemas.py` |
| L5 | 6:45 | Second reading by the other reader, and merging the two readings | B6 | `extract.py` |
| L6 | 7:00 | Full test with the printed ads and text offers on the server laptop | | none |

### Claude Code teammate
| # | Target | Item | Task | File |
|---|---|---|---|---|
| T1 | 5:45 | `cross_check`, `fill_gaps`, `compute` + tests | B3, B4 | `maths.py`, `test_maths.py` |
| T2 | 6:00 | `decide` + tests | B5 | `verdict.py`, `test_verdict.py` |
| T3 | 6:20 | `speech_text`, `make_audio` + tests | D2 | `speak.py`, `test_speak.py` |
| T4 | 6:45 | Bot: verdict line on the card, MP3 after the card, pasted text offers, Hindi error messages | D3, D4 | `bot/main.py` |

### PWA teammate
| Target | Item |
|---|---|
| 5:45 | `RajuCard` component showing the sample check from the API |
| 6:15 | `/check`: photo upload + text box -> card + audio player |
| 6:45 | Loading, error and not-a-loan states; Raju mode toggle; pushed |

The API already answers every call with a sample check, so the page can be built and tested now. Real answers arrive at about 6:30 with no change on the web side.

### Data teammate
| Target | Item |
|---|---|
| 6:00 | 3 demo ads printed in colour, two copies each, and `api/data/offers/demo_expected.json` |
| 6:15 | 5 text offers with expected numbers in `api/data/offers/sms_offers.json` |
| after the review | `api/data/rbi_dla.csv` filled in (the lender check is skipped tonight) |

## Merge point: 6:30 PM

At 6:30 the lead's `api/main.py` starts importing the teammate's `maths.py`, `verdict.py` and `speak.py`. For that to work, T1, T2 and T3 must be on main by 6:20, with the signatures below unchanged. The bot (T4) and the web page join at 6:45. **Hard stop 7:00 PM:** everything merged, `pytest` green, one real photo and one real text offer answered on the server laptop. After 7:00, nobody pushes without telling the lead.

## Agreed signatures

`fields` is always a dict with exactly these keys; a value is a number, a string, or `None` when it was not clearly written:
`is_loan_ad, principal, in_hand, fees, repay_total, emi_amount, emi_count, tenure_days, lender_name, app_name`

A number on the card is `{"value": 3800, "status": "derived"}`. Status is `read`, `derived`, `computed` or `unverified` (then value is `None`).

```python
# api/core/fallback.py (lead). The only file that calls outside services.
class EngineError(Exception): ...          # every engine that was tried has failed
def read_image(image_bytes: bytes, engines: tuple[str, ...] = ("qwen", "gemini")) -> tuple[str, str, float]
                                           # -> (raw reply, engine name, seconds)
def read_text(prompt: str) -> tuple[str, str, float]     # gpt-oss-20b
async def speak(text: str, out_path: str) -> bool         # True if the MP3 file was written

# api/core/extract.py (lead)
class NotALoan(Exception): ...             # the reader says this is not a loan offer
class Unreadable(Exception): ...           # no reader gave valid fields
def extract_from_image(image_bytes: bytes) -> dict
def extract_from_text(text: str) -> dict
    # both -> {"fields": {...}, "engines": {"read": "qwen", "second_read": None}}
    # read is "qwen" | "gemini" | "gpt-oss-20b" | "regex"
def second_reading(image_bytes: bytes, first: dict, problems: list[str]) -> tuple[dict, list[str]]
    # -> (the first result with engines.second_read filled, names of disputed fields)
    # disputed = number fields where the two readers differ by more than Rs 1,
    #            or where one reader saw a number and the other saw none.
    # If the other reader fails: second_read stays None and disputed = problems.

# api/core/maths.py (teammate)
def cross_check(fields: dict) -> list[str]
    # names of the fields in every sum that fails by more than Rs 1; [] when all is fine.
    # principal - fees != in_hand            -> ["principal", "fees", "in_hand"]
    # emi_amount * emi_count != repay_total  -> ["emi_amount", "emi_count", "repay_total"]
    # A sum is only checked when all three of its numbers are present.
def fill_gaps(fields: dict, disputed: list[str] = ()) -> dict
    # -> {"in_hand": {...}, "repay_total": {...}, "tenure_days": {...}}
def compute(numbers: dict) -> dict
    # -> the same three plus "extra", "per_day", "apr_simple" (the "numbers" block of CheckResult)

# api/core/verdict.py (teammate)
def decide(numbers: dict, fees: float | None) -> str   # USUAL | COSTLY | VERY_COSTLY | CANNOT_SAY

# api/core/speak.py (teammate)
def speech_text(numbers: dict) -> str
async def make_audio(check_id: str, text: str) -> str | None
    # writes <AUDIO_DIR>/<check_id>.mp3 through fallback.speak
    # -> "/api/audio/<check_id>.mp3", or None if voice is switched off or failed
```

Changed from the earlier agreement: `read_image` takes a list of engines (the second reading needs "only the other one"), `fill_gaps` takes `disputed`, and `second_reading` is new.

### How the lead's `api/main.py` uses them

```python
first = extract_from_image(image)                 # or extract_from_text(text)
fields, disputed = first["fields"], []
problems = cross_check(fields)
if problems and it_was_a_photo:
    first, disputed = second_reading(image, first, problems)
# set every disputed field to None, then check again; a sum that still fails
# (both readers agree, so the ad contradicts itself) adds its fields to disputed
numbers = compute(fill_gaps(fields, disputed))
verdict = decide(numbers, None if "fees" in disputed else fields["fees"])
text    = speech_text(numbers)
audio   = await make_audio(check_id, text)        # None -> the card goes out alone
```

For a text offer there is no second reader, so a sum that fails makes its fields "couldn't verify" directly.

### Rules inside the maths (teammate)

- A field named in `disputed` counts as missing.
- `in_hand`: principal and fees both present -> principal - fees, `derived`. Otherwise a written in_hand -> `read`. Otherwise principal alone (no fee written on the ad) -> principal, `derived`. Otherwise `unverified`.
- `repay_total`: written -> `read`. Otherwise emi_amount x emi_count -> `derived`. Otherwise `unverified`.
- `tenure_days`: written and above 0 -> `read`. Otherwise `unverified`.
- `extra` = repay_total - in_hand. `per_day` = extra / tenure_days. `apr_simple` = extra / in_hand x 365 / tenure_days x 100, a percentage. All three are rounded to a whole number, status `computed`.
- If an input is `unverified`, or extra comes out below 0, the outputs that need it are `unverified`. Never a division error.
- `decide`: `CANNOT_SAY` if in_hand, repay_total, tenure_days or apr_simple is unverified. `VERY_COSTLY` if apr_simple > 100, or fees > 0 on a loan of 30 days or less. `COSTLY` if apr_simple >= 36. Otherwise `USUAL`. Thresholds come from `config.py`.
- `speech_text`: the fixed sentence from CLAUDE.md, whole numbers, no commas. If in_hand, repay_total, tenure_days or extra is unverified, say instead: "Is offer ke saare number saaf nahi padhe gaye. Loan lene se pehle bank mitra se poochho."

### Small API additions (D26)

- `lender.match` is `null` tonight, meaning "not checked". The card hides the lender line when it is null. We never show "Not found" for a check we did not run.
- `next_step` is fixed: `{"code": "ASK_BANK_MITRA", "text_hi": "Loan lene se pehle bank mitra se poochho."}`
- When there is no card, `POST /api/checks` answers with status 422 and `{"detail": {"code": "NOT_A_LOAN" | "UNREADABLE", "text_hi": "<Hindi message to show>"}}`. The bot and the web page show `text_hi` as it is.
- `audio_url` can be `null`. Then there is no MP3: hide the player, send the card alone.

## Tests with hand-worked values

Worked by hand before any code exists. `-` means the ad does not print it.

| # | Case | principal | fees | in_hand | repay | EMI | days | -> in_hand | repay | extra | per_day | apr % | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Fee taken upfront | 5000 | 1200 | - | 5000 | - | 7 | 3800 derived | 5000 read | 1200 | 171 | 1647 | VERY_COSTLY |
| 2 | Plain, cheap | 10000 | - | - | 10250 | - | 30 | 10000 derived | 10250 read | 250 | 8 | 30 | USUAL |
| 3 | Plain, dear | 10000 | - | - | 10600 | - | 30 | 10000 derived | 10600 read | 600 | 20 | 73 | COSTLY |
| 4 | EMI, total printed | 20000 | - | - | 24000 | 2000 x 12 | 360 | 20000 derived | 24000 read | 4000 | 11 | 20 | USUAL |
| 5 | EMI, total not printed | 20000 | - | - | - | 2000 x 12 | 360 | 20000 derived | 24000 derived | 4000 | 11 | 20 | USUAL |
| 6 | Small fee, short loan | 10000 | 100 | - | 10000 | - | 30 | 9900 derived | 10000 read | 100 | 3 | 12 | VERY_COSTLY (fee rule) |
| 7 | In-hand printed | 5000 | - | 4500 | 5600 | - | 7 | 4500 read | 5600 read | 1100 | 157 | 1275 | VERY_COSTLY |
| 8 | Days missing | 5000 | 1200 | - | 5000 | - | - | 3800 derived | 5000 read | 1200 | unverified | unverified | CANNOT_SAY |
| 9 | Zero days | 5000 | 1200 | - | 5000 | - | 0 | 3800 derived | 5000 read | 1200 | unverified | unverified | CANNOT_SAY, no error |
| 10 | Repay disputed | 5000 | 1200 | - | disputed | - | 7 | 3800 derived | unverified | unverified | unverified | unverified | CANNOT_SAY |

More tests:
- **Cross-check.** 5000 / 1200 / in_hand 4000 -> `["principal", "fees", "in_hand"]`. In_hand 3801 -> `[]` (within Rs 1). EMI 2000 x 12 with repay 25000 -> `["emi_amount", "emi_count", "repay_total"]`. Only principal and repay present -> `[]`.
- **Verdict edges.** apr 35 -> USUAL, 36 -> COSTLY, 100 -> COSTLY, 101 -> VERY_COSTLY. Setting `band_costly_apr` to 20 turns row 2 into COSTLY without touching code.
- **Speech.** Row 1 -> "Aapko haath mein 3800 rupaye milenge. 7 din mein 5000 rupaye lautane honge. Yaani 1200 rupaye zyada." Row 8 -> the "saaf nahi padhe gaye" sentence.
- **Audio.** `make_audio` with `fallback.speak` replaced by a fake: returns `/api/audio/chk_0001.mp3` when it succeeds, `None` when it fails or when `VOICE_ENABLED=false`.
- **Fences.** `strip_fences('```json\n{"principal": 5000}\n```')` -> `{"principal": 5000}`.
- **Second reading.** First reader: row 1 plus an invented in_hand 4000. Second reader: row 1 with no in_hand. Disputed = `["in_hand"]`, the result is row 1 again, VERY_COSTLY, `second_read` filled.
- **A self-contradicting ad.** Both readers see 5000 / 1200 / in_hand 4000 -> in_hand unverified -> CANNOT_SAY.
- **Second reader down.** Same photo, the other reader fails -> the three fields in the failed sum are unverified -> CANNOT_SAY.
- **Text, AI down.** "Loan Rs 5000. Fee Rs 500. Repay Rs 5600 in 7 days." with `read_text` failing -> regex gives principal 5000, fees 500, repay 5600, days 7 -> in_hand 4500, extra 1100, per_day 157, apr 1275, VERY_COSTLY, `engines.read` = "regex".
- **Not a loan.** The reader returns `is_loan_ad: false` -> status 422 with code `NOT_A_LOAN`.
- **Fallback.** Qwen answers 429 -> Gemini is called at once and `engines.read` = "gemini". Both fail -> 422 with code `UNREADABLE`.

No test calls a real AI service or the internet; the tests replace `fallback` functions with fakes.

## Rehearsal checklist (7:00 to 7:30 PM, server laptop, demo bot)

- [ ] `git pull`, `pytest -q` green, API and bot started, `/api/health` shows all three keys set
- [ ] Only the server laptop is running the demo bot token
- [ ] Round 1: ad 1, ad 2, ad 3 photographed in Telegram -> card + voice each time, numbers match `demo_expected.json`
- [ ] Round 2: the same three again -> same numbers
- [ ] Text offer 1 and 2 pasted in Telegram -> card + voice, twice
- [ ] One photo and one text offer on `/check` on a phone -> card + audio plays
- [ ] A photo that is not a loan ad -> a polite Hindi message, no card
- [ ] `VOICE_ENABLED=false` -> the card still arrives
- [ ] Note the seconds per check and the Groq photo reads left

Six photo reads in a row is more than Groq's free limit of about 3 a minute, so some answers will come from Gemini and take about 8 seconds. Leave 20 seconds between photos if you want Qwen every time.

## Ready-to-paste prompts

### For the Claude Code teammate

```
Read AGENTS.md, CLAUDE.md and docs/PLAN.md first, then docs/PROGRESS.md and docs/DECISIONS.md (D25, D26). Follow "How to report while working" in CLAUDE.md.

You are doing the "Claude Code teammate" row of docs/PLAN.md. You may edit ONLY these files:
api/core/maths.py, api/core/verdict.py, api/core/speak.py, bot/main.py,
api/tests/test_maths.py, api/tests/test_verdict.py, api/tests/test_speak.py
Do not edit any other file (not api/main.py, fallback.py, extract.py, schemas.py, config.py, web/, docs/PLAN.md). If you think another file must change, stop and tell me; the lead owns it.

Do these in order, one at a time. After each: run pytest -q, show the output, commit as "<area>: <what changed>", pull main, push (a branch + pull request if the push is refused).
T1 by 5:45 PM: maths.py: cross_check, fill_gaps, compute, with test_maths.py (tasks B3, B4).
T2 by 6:00 PM: verdict.py: decide, with test_verdict.py (task B5). Thresholds come from settings in config.py; do not hard-code them.
T3 by 6:20 PM: speak.py: speech_text, make_audio, with test_speak.py (task D2). Call fallback.speak for the audio; never import edge-tts yourself. In tests, replace fallback.speak with a fake.
T4 by 6:45 PM: bot/main.py (tasks D3, D4): add a verdict line to the card; after the card, download audio_url from the API and send it with sendAudio (no ffmpeg, no sendVoice); if audio_url is null or the download fails, send the card alone; a plain text message is posted to /api/checks as JSON {"text", "lang": "hi", "source": "telegram"}; on status 422 reply with detail.text_hi; hide the lender line when lender.match is null.

Use the signatures and the "Rules inside the maths" section of docs/PLAN.md exactly; the lead's code calls them at 6:30 PM. Use the hand-worked table in docs/PLAN.md (rows 1 to 10, plus the cross-check, verdict-edge, speech and audio cases) as your tests, with those exact values. No test may call the internet.

Hard stop 7:00 PM. When done, add an entry at the top of docs/PROGRESS.md and set your tasks to "review" in docs/TASKS.md (those two doc files are the only exception to the file list).
```

### For the PWA teammate (Antigravity)

```
Read AGENTS.md, CLAUDE.md and docs/PLAN.md first. You may edit ONLY files inside web/src/. Do not touch anything outside web/src/ (no api/, bot/, docs/, no package.json, no config files). Do not add any npm package: use what is installed (React, Tailwind, shadcn/ui, lucide-react). No animation libraries.

Build the /check page of the helper web app for the 7:30 PM review:
1. web/src/components/RajuCard.tsx: ONE card component, used everywhere a result is shown. It takes a CheckResult (shape in CLAUDE.md). It shows four big numbers with an icon and a colour each: in hand, to repay, days, extra. Numbers are 36 to 48 px. A verdict badge: USUAL, COSTLY, VERY_COSTLY, CANNOT_SAY, each with a colour AND an icon. Any number whose status is "unverified" shows a grey "couldn't verify" chip, never a 0 and never a guess. Show next_step.text_hi. Hide the lender line when lender.match is null.
2. web/src/pages/Check.tsx: a photo upload (on a phone it opens the camera or gallery) and a text box for a pasted SMS offer. Photo -> POST /api/checks as form data with the field "image", plus lang=hi and source=web. Text -> POST /api/checks as JSON {"text": "...", "lang": "hi", "source": "web"}. Show the RajuCard and an audio player for audio_url (the URL is relative to the API address; hide the player when audio_url is null).
3. States: loading (the answer can take 10 seconds), server off, and status 422 where the body is {"detail": {"code": "NOT_A_LOAN" or "UNREADABLE", "text_hi": "..."}}: show text_hi as it is. Never show an error code to the user.
4. A "Raju mode" toggle: details hidden, one big camera button and one big play button, every button at least 56 px tall.
It must look right at 400 px wide, in light and dark.

The API already answers every request with a sample check, so you can build and test now; real answers start at about 6:30 PM with no change needed. Put shared types and fetch calls in web/src/lib/api.ts.
Targets: RajuCard by 5:45 PM, /check by 6:15 PM, states and Raju mode pushed by 6:45 PM. Before pushing run "npm run build" inside web/ and fix every error. Push on a branch and open a pull request; tell the lead.
```

### For the data teammate (Antigravity)

```
Read AGENTS.md, CLAUDE.md and docs/PLAN.md first. You may edit ONLY files inside api/data/. Do not touch any other folder. Synthetic data only: invented lender names, no real people, no real phone or Aadhaar numbers.

1. By 6:00 PM: three loan ads for the live demo, as images in api/data/offers/ (ad1.png, ad2.png, ad3.png), then printed in colour, two copies each. They should look like real loan-app ads, with every number printed large in digits and the loan length printed in DAYS.
   - ad1: a fee taken upfront on a short loan. Prints: loan amount, processing fee, amount to repay, days. Example: loan 5000, fee 1200, repay 5000 in 7 days.
   - ad2: a plain loan with no fee. Prints: loan amount, amount to repay, days.
   - ad3: an EMI loan. Prints: loan amount, EMI amount, number of EMIs, total to repay, days. EMI x number must equal the total.
   Write the expected answers BY HAND (a calculator is fine, no AI) in api/data/offers/demo_expected.json:
   [{"file": "ad1.png", "principal": 5000, "fees": 1200, "in_hand": 3800, "repay_total": 5000, "tenure_days": 7, "extra": 1200}]
   where in_hand = loan amount minus fee, and extra = repay_total minus in_hand.
2. By 6:15 PM: five SMS-style text offers in api/data/offers/sms_offers.json, a mix of English and Hinglish, each stating a loan amount, the amount to repay and the days (some with a fee, one with EMIs):
   [{"id": "sms1", "text": "...", "expected": {"in_hand": 4500, "repay_total": 5600, "tenure_days": 7, "extra": 1100}}]
3. After those: fill api/data/rbi_dla.csv from RBI's public directory of digital lending apps. Keep the header dla_name,regulated_entity,list_date and put the date of the list in every row. This is needed after the review, not before it.

Write expected numbers before anyone runs the app on the ads. Do not change any existing file except api/data/rbi_dla.csv and api/data/README.md. Push on a branch and open a pull request; hand the printed ads to the lead by 6:00 PM.
```
