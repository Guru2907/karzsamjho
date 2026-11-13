# PLAN.md: the plan for the 7:30 PM review (written 13 Nov, 5:00 PM IST)

This replaces the earlier split. Decision D25 in docs/DECISIONS.md. If this file and the code disagree, trust the code and fix this file.

## Status at 6:30 PM

- **Backend + bot: done and merged** (PRs #1 to #11). Photo or SMS in Telegram -> card + Hindi MP3, with the second reading. 152 tests pass on main.
- Lead L1 to L5 and Siddeshwar T1 to T4 finished by 5:50 PM. Siddeshwar's bot got three small fixes after review (#11).
- **Not arrived yet:** the PWA teammate's web PRs (`/check` still shows the placeholder) and the data teammate's printed ads and SMS offers (`api/data/offers/` is empty).
- **Still to do before 7:30:** real Telegram on the server laptop with the demo bot; the 3 printed ads twice; the rehearsal checklist below.

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
| Lead (Gurpreet) | Claude Code | Calls to the AI services, reading photos and text, second reading, joining everything in the API | `api/core/fallback.py`, `api/core/extract.py`, `api/core/schemas.py`, `api/main.py`, `api/tests/test_extract.py`, `api/tests/test_pipeline.py`, `api/tests/test_smoke.py`, `docs/` |
| Claude Code teammate (Siddeshwar) | Claude Code | Rupee maths, verdict, Hindi sentence + MP3, Telegram bot | `api/core/maths.py`, `api/core/verdict.py`, `api/core/speak.py`, `bot/main.py`, `api/tests/test_maths.py`, `api/tests/test_verdict.py`, `api/tests/test_speak.py` |
| PWA teammate | Antigravity | The web app: `/check` page, the Raju card, home-screen app setup | `web/src/`, `web/public/`, `web/index.html` only |
| Data teammate | Antigravity | Printed demo ads, text offers, 30 test offers, harassment samples, RBI list, vendor notes, backup video | `api/data/` only |

Nobody edits a file in another person's row. If you need a change there, ask that person.

**Getting code onto main (D27):** nobody pushes to main. For each finished item: pull main, make a branch, push it, open a pull request. CI (tests, web build, key scan) must be green. Then tell Gurpreet; he merges. One small PR per item, never one big PR at 6:55.

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
| 6:45 | Loading, error and not-a-loan states; Raju mode toggle; home-screen app setup (manifest + icons) |

The API already answers every call with a sample check, so the page can be built and tested now. Real answers arrive at about 6:30 with no change on the web side.

### Data teammate
| Target | Item |
|---|---|
| 6:00 | 3 demo ads printed in colour, two copies each, and `api/data/offers/demo_expected.json` |
| 6:15 | 5 text offers with expected numbers in `api/data/offers/sms_offers.json` |
| 9:00 | 30 test offers with answers (G1) |
| 10:00 | 10 harassment samples with expected rules (G2) |
| after that | `api/data/rbi_dla.csv` filled in (G4) |
| 7:00 to 7:30 | Screen-record the rehearsal as the backup video (I3); 3 mentor questions written before 7:30 (I1) |

## Merge point: 6:30 PM

At 6:30 the lead's `api/main.py` starts importing the teammate's `maths.py`, `verdict.py` and `speak.py`. For that to work, T1, T2 and T3 must be on main by 6:20, with the signatures below unchanged. The bot (T4) and the web page join at 6:45. **Hard stop 7:00 PM:** everything merged, `pytest` green, one real photo and one real text offer answered on the server laptop. After 7:00, nobody pushes without telling the lead.

## Agreed signatures

`fields` is always a dict with exactly these keys; a value is a number, a string, or `None` when it was not clearly written:
`is_loan_ad, principal, in_hand, fees, repay_total, emi_amount, emi_count, tenure_days, lender_name, app_name`

A number on the card is `{"value": 3800, "status": "derived"}`. Status is `read`, `derived`, `computed` or `unverified` (then value is `None`).

```python
# api/core/fallback.py (lead). The only file that calls outside services.
class EngineError(Exception): ...          # every engine that was tried has failed
def read_image(image_bytes: bytes, prompt: str, engines: tuple[str, ...] = ("qwen", "gemini"),
               check: Callable[[str], Any] | None = None) -> tuple[str, str, float]
                                           # -> (raw reply, engine name, seconds)
                                           # check(raw) raising = that engine failed, try the next
def read_text(prompt: str, check=None) -> tuple[str, str, float]   # gpt-oss-20b only
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

## After the review: Gurpreet + Siddeshwar split (written 6:50 PM, D34)

The PWA teammate keeps all of `web/` (E2 to E9). The data teammate keeps all of `api/data/` (G1 to G4, G8) plus I1 and I3. This section splits the backend and bot work that is left between Gurpreet and Siddeshwar. **Nobody edits a file in the other person's list.**

| Person | Only these files |
|---|---|
| Gurpreet | `api/main.py`, `api/core/schemas.py`, `api/core/config.py`, `api/core/fallback.py`, `api/core/cache.py`, `api/core/db.py`, `api/core/lender.py`, `api/core/next_step.py`, `api/core/extract.py`, and their tests |
| Siddeshwar | `bot/main.py`, `api/core/speak.py`, `api/core/harass.py`, `api/core/evidence.py`, `api/core/maths.py`, `api/core/verdict.py`, and their tests |

### Order (musts first; stretch only after the 7:30 gate has passed)

| # | Gurpreet | Siddeshwar |
|---|---|---|
| now | **Seconds stamp** on the Telegram card ("⏱ 3.9 sec", for DEMO LIVE 1; one-off edit of bot/main.py before Siddeshwar starts on it), then **A4** cache: a repeated photo answers instantly, no AI call | **F1** harass.py: rules H1 to H6 + keyword backup (`fallback.read_text` for the AI labels) |
| 1 | **A3** db.py: checks, cases, events survive a restart | (F1 continued) |
| 2 | **A5** health (engines up/down) + stats from the database | **F3** evidence.py: English PDF, hashes, masking, complaint draft |
| 3 | **F2** events endpoint + hash chain, **F4** verify | **D5** bot: forwarded message -> case event -> PDF back in the chat |
| 4 | **C1** lender.py (needs G4 CSV), **C2** next step, **F5** complaint route + day counter | |
| after gate | **D6 backend**: `audio` field, Whisper, number words -> digits | **D6 bot**: voice notes -> API |
| after gate | **D7 backend**: `lang` passed through, voices in config | **D7**: Bengali + Marathi templates in speak.py, language choice in the bot |

12:30 AM gate needs every "1 to 4" row. D6 and D7 are stretch: start them only when your musts are merged, and stop at 3:30 AM.

### Agreed signatures (after the review)

```python
# api/core/cache.py (Gurpreet)
def image_key(image_bytes: bytes) -> str                 # SHA-256 hex
def get(key: str) -> dict | None                        # stored CheckResult (+ its MP3 still on disk)
def put(key: str, result: dict) -> None

# api/core/harass.py (Siddeshwar), task F1
def label(event: dict, calls_that_day: int) -> list[str]
    # event = {"at": ISO time with +05:30, "channel", "contacted", "text"}
    # calls_that_day = calls to this case on that date INCLUDING this one (Gurpreet counts it from db)
    # -> sorted rule ids, e.g. ["H1", "H2"]; [] for the polite 11 AM reminder
    # H1 and H6 by code only; H2 to H5 by fallback.read_text with a keyword-list backup

# api/core/evidence.py (Siddeshwar), task F3
def mask(text: str) -> str                               # any 12-digit number -> "XXXX XXXX 1234"
def build_pdf(case: dict) -> bytes                      # case = GET /api/cases/{id} shape (events with rules,
                                                         # hash, prev_hash; route; day); English only

# api/core/next_step.py (Gurpreet), tasks C2, F5
def next_step(verdict: str, lender_match: str | None) -> dict        # {"code", "text_hi"}
def complaint_route(lender_match: str | None, has_threats: bool) -> str

# api/core/fallback.py (Gurpreet), task D6
def transcribe(audio_bytes: bytes) -> tuple[str, str, float]         # (text, "whisper", seconds)
async def speak(text: str, out_path: str, voice: str | None = None) -> bool   # voice None = Hindi

# api/core/speak.py (Siddeshwar), task D7: lang is "hi" (default), "bn" or "mr"
def speech_text(numbers: dict, lang: str = "hi") -> str
async def make_audio(check_id: str, text: str, lang: str = "hi") -> str | None
    # picks the voice with config.settings.tts_voice(lang)
```

### API additions (D33)
- `POST /api/checks` also takes a form field `audio` (a Telegram voice note, OGG). The API transcribes it with Whisper, gpt-oss-20b turns number words into digits (D22), then it is read like a pasted SMS.
- `engines` gets one optional field, `listen` ("whisper" or null). Additive: nothing that reads the old shape breaks.
- `lang` (already in the contract) now picks the voice: `hi` (default), `bn`, `mr`. The card and Telegram text stay in Hinglish; only the voice changes (D7: "one voice and one template" per language).

### Bengali and Marathi sentences (D32): a native speaker checks these before D7 is merged

Same meaning as the Hindi template. Native script, so the voices read them properly. Numbers in digits.
- **bn** (voice bn-IN-TanishaaNeural): "আপনি হাতে {in_hand} টাকা পাবেন। {days} দিনে {repay} টাকা ফেরত দিতে হবে। মানে {extra} টাকা বেশি।"
- **bn**, numbers not clear: "এই অফারের সব সংখ্যা পরিষ্কার পড়া যায়নি। লোন নেওয়ার আগে ব্যাংক মিত্রকে জিজ্ঞেস করুন।"
- **mr** (voice mr-IN-AarohiNeural): "तुम्हाला हातात {in_hand} रुपये मिळतील. {days} दिवसांत {repay} रुपये परत करावे लागतील. म्हणजे {extra} रुपये जास्त."
- **mr**, numbers not clear: "या ऑफरचे सगळे आकडे नीट वाचता आले नाहीत. कर्ज घेण्याआधी बँक मित्राला विचारा."

### Prompt for Siddeshwar (after-review work)

```
I am Siddeshwar. Read AGENTS.md, CLAUDE.md, then docs/PLAN.md section "After the review", then the top of docs/PROGRESS.md and docs/DECISIONS.md D28 to D34. Follow "How to report while working" in CLAUDE.md.

You may edit ONLY: bot/main.py, api/core/speak.py, api/core/harass.py, api/core/evidence.py, api/core/maths.py, api/core/verdict.py, their tests in api/tests/, plus your own entry in docs/PROGRESS.md and your task statuses in docs/TASKS.md. Gurpreet owns every other file (main.py, schemas.py, config.py, fallback.py, cache.py, db.py, lender.py, next_step.py, extract.py). If you need a change there, stop and tell me.

One task at a time, in this order. Before each, say "We are doing <task>". After each: pytest -q (show output), pull main, branch, commit "<area>: <what changed>", push, gh pr create, gh pr checks. Never push to main, never merge (Gurpreet merges). No Claude co-author line.
(The seconds stamp on the card is done by Gurpreet; pull main before you touch bot/main.py.)
1. F1 harass.py: label(event, calls_that_day) exactly as in docs/PLAN.md. H1 before 08:00 or after 19:00 (hours from config). H6 when calls_that_day >= config h6_calls_per_day (label it "our threshold"). H2 to H5 with fallback.read_text (temperature 0 JSON, check= a parser) and a keyword-list backup in Hinglish and English when the AI fails. Tests with hand-written samples; the polite 11 AM reminder gets [].
2. F3 evidence.py: mask() and build_pdf(case) with ReportLab, ENGLISH only (no Devanagari). Timeline, rules with their basis (RBI circular on recovery agents, 12 Aug 2022), each event's hash and prev_hash, masked 12-digit numbers, complaint draft, route, "Day N of 30". Test: a 12-digit number is masked; the PDF starts with %PDF.
3. D5 bot: a forwarded message (or a plain message after /log) becomes an event: POST /api/cases once per chat (remember the case id), POST /api/cases/{id}/events with at = the original message time, channel "telegram", contacted "borrower", text; then GET /api/cases/{id}/evidence.pdf and send it with reply_document. Hindi messages only.
4. After the 7:30 gate and only when 1 to 3 are merged: D6 bot side (voice note -> POST /api/checks with form field "audio") and D7 (speak.py templates for bn and mr from docs/PLAN.md, speech_text(numbers, lang), make_audio(check_id, text, lang); in the bot a /bhasha command with three buttons Hindi / Bangla / Marathi, remembered per chat and sent as lang). A native speaker checks the bn and mr sentences before the PR.
Stop all features at 3:30 AM.
```

## Ready-to-paste prompts

Each person pulls main, then pastes their prompt into their own agent (Claude Code or Antigravity) opened in the repo folder.

### For Siddeshwar (Claude Code teammate)

```
I am Siddeshwar. In docs/PLAN.md I am the "Claude Code teammate"; Gurpreet is the "Lead".

Read AGENTS.md, CLAUDE.md and docs/PLAN.md first, then docs/PROGRESS.md and docs/DECISIONS.md (D25, D26, D27). Follow "How to report while working" in CLAUDE.md.

You are doing the "Claude Code teammate" row of docs/PLAN.md. You may edit ONLY these files:
api/core/maths.py, api/core/verdict.py, api/core/speak.py, bot/main.py,
api/tests/test_maths.py, api/tests/test_verdict.py, api/tests/test_speak.py
Do not edit any other file (not api/main.py, fallback.py, extract.py, schemas.py, config.py, web/, docs/PLAN.md). If you think another file must change, stop and tell me; Gurpreet owns it.

Do these in order, one at a time. Before each, tell me "We are doing <task>". After each: run pytest -q and show the output; pull main; make a branch; commit as "<area>: <what changed>"; push the branch; open a pull request with gh pr create; check CI with gh pr checks. Never push to main and never merge: Gurpreet merges. Never add Claude as co-author or a "Generated with Claude Code" line.
T1 by 5:45 PM: maths.py: cross_check, fill_gaps, compute, with test_maths.py (tasks B3, B4).
T2 by 6:00 PM: verdict.py: decide, with test_verdict.py (task B5). Thresholds come from settings in config.py; do not hard-code them.
T3 by 6:20 PM: speak.py: speech_text, make_audio, with test_speak.py (task D2). Call fallback.speak for the audio; never import edge-tts yourself. In tests, replace fallback.speak with a fake.
T4 by 6:45 PM: bot/main.py (tasks D3, D4): add a verdict line to the card; after the card, download audio_url from the API and send it with sendAudio (no ffmpeg, no sendVoice); if audio_url is null or the download fails, send the card alone; a plain text message is posted to /api/checks as JSON {"text", "lang": "hi", "source": "telegram"}; on status 422 reply with detail.text_hi; hide the lender line when lender.match is null.

Use the signatures and the "Rules inside the maths" section of docs/PLAN.md exactly; Gurpreet's code calls them at 6:30 PM. Use the hand-worked table in docs/PLAN.md (rows 1 to 10, plus the cross-check, verdict-edge, speech and audio cases) as your tests, with those exact values. No test may call the internet.

Hard stop 7:00 PM. In each PR, add an entry at the top of docs/PROGRESS.md and set the task to "review" in docs/TASKS.md (those two doc files are the only exception to the file list).

Start by telling me in 3 lines which task you are on, which files you will touch and how you will prove it works. Then begin T1.
```

### For the PWA teammate (Antigravity)

```
Read AGENTS.md, CLAUDE.md and docs/PLAN.md first, then the top of docs/PROGRESS.md and decisions D25 to D27 in docs/DECISIONS.md.

YOUR FILES. You may edit ONLY:
- anything inside web/src/
- web/public/ (manifest and icons)
- web/index.html
Do not touch api/, bot/, docs/ (except the two lines at the end), web/package.json, web/vite.config.ts or any other config file. Do not add any npm package. Use only what is installed: React 19, Tailwind 4, shadcn/ui components in web/src/components/ui/, lucide-react icons, sonner. No animation libraries, no service worker, no offline mode, no login.

WHAT YOU ARE BUILDING. A web app that feels like a phone app, for Raju (a vegetable vendor who cannot read loan terms) and the helper sitting next to him. He photographs a loan ad or pastes an SMS, and sees and hears what he gets, what he repays and how much extra that is. Hindi first, in Latin letters (Hinglish), with small English below where it helps.

RUN IT. In web/: npm ci, then npm run dev. Open http://localhost:5173/check. The API runs on port 8000 (ask Gurpreet, or run scripts/run_api); the dev server already passes every /api call to it. Right now the API always answers with one sample check (chk_0042). Real answers start about 6:30 PM with no change on your side. To try it on a phone, open http://<laptop wifi address>:5173/check on the same wifi.

STEP 1 (by 5:45 PM): web/src/components/RajuCard.tsx
- ONE component, used everywhere a result is shown. Props: { result: CheckResult; raju?: boolean }. Types are in web/src/lib/api.ts.
- Four rows, each with an icon, a colour and a big number (36 to 48 px, tabular figures, rupees with the ₹ sign and Indian commas: ₹3,800):
  - haath mein (in hand): numbers.in_hand, green, lucide HandCoins
  - lautana hai (to repay): numbers.repay_total, blue, lucide Undo2
  - din (days): numbers.tenure_days, neutral, lucide CalendarDays
  - zyada (extra): numbers.extra, red, lucide TriangleAlert
- A number whose status is "unverified" (or value null) shows a grey chip "pata nahi chala / couldn't verify". Never a 0, never a guess.
- A verdict badge at the top, colour AND icon together: USUAL "Theek hai" green CircleCheck; COSTLY "Mehenga" amber CircleAlert; VERY_COSTLY "Bahut mehenga" red OctagonAlert; CANNOT_SAY "Keh nahi sakte" grey CircleHelp.
- next_step.text_hi as a line under the numbers.
- Lender line: hide it completely when lender.match is null (tonight it is always null).
- When raju is false, a small details section under the card: per_day and apr_simple (label apr_simple "saal ka hisaab, %"; it is our own estimate, not an RBI number), engines.read, seconds.
- Check: the sample check shows ₹3,800 / ₹5,000 / 7 din / ₹1,200 and "Bahut mehenga", at 400 px wide, in light and dark.

STEP 2 (by 6:15 PM): web/src/pages/Check.tsx
- Replace the placeholder. Two ways in:
  - A big "Photo lo" button: a hidden <input type="file" accept="image/*" capture="environment">; on a phone it opens the camera. A smaller "Gallery se" button without capture.
  - A text box "SMS yahan chipkao" with a "Bhejo" button.
- Photo -> api.checkImage(file). Text -> api.checkText(text). Both already exist in web/src/lib/api.ts.
- While waiting: a large spinner made with Tailwind only (animate-spin) and "Padh rahe hain…". The answer can take up to 15 seconds. Disable the buttons meanwhile.
- Then: the RajuCard, then an <audio controls> player for audio_url (hide it when audio_url is null), then a "Naya check" button that clears everything.
- audio_url is like "/api/audio/chk_0001.mp3"; use it as it is (the dev server passes it on).

STEP 3 (by 6:45 PM): errors, Raju mode, home-screen app
- Errors in web/src/lib/api.ts. Change request() so that:
  - a 422 answer throws an error that carries body.detail.text_hi;
  - a network failure throws an error with "Server abhi band hai, thodi der mein try karo.";
  - anything else throws "Kuch gadbad hui, dobara try karo.".
  Show that text in the page, big, with a "Dobara try karo" button. Never show a status code or English error text to the user.
  The 422 body looks like {"detail": {"code": "NOT_A_LOAN" | "UNREADABLE", "text_hi": "..."}}.
  Also make lender.match nullable in the CheckResult type (LenderMatch | null). Keep every other type as it is.
- Raju mode: a switch at the top of /check ("Raju mode"), remembered in localStorage (wrap it in try/catch). In Raju mode the page shows only: one huge camera button, the card with no details, and one huge play button for the audio. Every button at least 56 px tall.
- Home-screen app (task E6):
  - web/public/manifest.json: name "KarzSamjho", short_name "KarzSamjho", start_url "/check", display "standalone", background_color and theme_color matching the app, icons 192x192 and 512x512 PNG (draw a simple icon: a ₹ sign on a coloured rounded square; make an SVG, export both sizes; also save it as apple-touch-icon.png 180x180).
  - web/index.html: add <link rel="manifest" href="/manifest.json">, <meta name="theme-color" content="...">, <link rel="apple-touch-icon" href="/apple-touch-icon.png">, and change the viewport to "width=device-width, initial-scale=1.0, viewport-fit=cover".
- App feel on a phone: the page fills the screen height (min-h-svh); padding respects the notch (env(safe-area-inset-*)); main actions sit in a bottom bar within thumb reach; nothing works only on hover; text at least 16 px; tap targets at least 56 px.

BEFORE EACH PULL REQUEST
- In web/: npm run build must finish with no errors.
- Look at /check at 400 px wide and at laptop width, in light and dark.
- On a phone over wifi: take a photo, see the card, play the audio. In Chrome, "Add to home screen" must open the app without the browser bar.

HANDING OVER. One pull request per step (3 in total). Never push to main and never merge. For each: pull main, make a branch, commit as "web: <what changed>", push, open a pull request, and tell Gurpreet. In the same pull request, add a short entry at the top of docs/PROGRESS.md and set the task status to "review" in docs/TASKS.md (E2 for step 1; E3 and E9 for step 2; E6 and E7 for step 3). Those two lines are the only docs you may touch.
Before each step, tell me in 3 lines what you will build, which files you will touch and how you will check it.
```

### For the data teammate (Antigravity)

```
Read AGENTS.md, CLAUDE.md and docs/PLAN.md first, especially the "Tests with hand-worked values" table in docs/PLAN.md.

YOUR FILES. You may edit ONLY files inside api/data/. Do not touch any other folder. Synthetic data only: invented app and lender names (except the real public RBI list in step 5), no real people, no real phone, Aadhaar or account numbers.

GOLDEN RULE: every expected answer is worked out BY HAND with a calculator before anyone runs the app. Never ask an AI to calculate an expected number. These files are how we prove the app never shows a wrong rupee number.

STEP 1 (by 6:00 PM): 3 demo ads for the live demo (task G3)
- Make them in Canva (free) or Google Slides, size 1080 x 1350 (phone ad). Make them look like real loan-app ads: bright colours, an invented app name and logo, "Instant loan in 5 minutes!", but every number printed large in digits and the loan length in DAYS.
  - ad1.png, a fee taken upfront: loan 5000, processing fee 1200, repay 5000, 7 days.
  - ad2.png, plain, no fee: loan 10000, repay 10600, 30 days.
  - ad3.png, EMI: loan 20000, EMI 2000 x 12, total repay 24000, 360 days.
- Save them in api/data/offers/. Print each in colour, two copies. Photograph each print with a phone (slight angle, normal room light) and save as ad1_photo.jpg, ad2_photo.jpg, ad3_photo.jpg. That is what Raju's photos look like.
- Write api/data/offers/demo_expected.json by hand:
  [{"file": "ad1.png", "principal": 5000, "fees": 1200, "in_hand": 3800, "repay_total": 5000, "tenure_days": 7, "extra": 1200, "verdict": "VERY_COSTLY"}, ...]
  in_hand = loan minus fee (or the loan if there is no fee). extra = repay minus in_hand. Use the verdict column of the PLAN.md table.
- Hand the printed copies to Gurpreet by 6:00 PM.

STEP 2 (by 6:15 PM): 5 SMS-style text offers (task G8), in api/data/offers/sms_offers.json
- A mix: 2 in English, 2 in Hinglish, 1 in Hindi script. One EMI offer. One with the fee written as a percentage ("processing fee 10%").
  [{"id": "sms1", "text": "Congrats! Rs 5000 loan approved. Fee Rs 500. Repay Rs 5600 in 7 days.", "expected": {"principal": 5000, "fees": 500, "in_hand": 4500, "repay_total": 5600, "tenure_days": 7, "extra": 1100}}, ...]
- Write null for a number the SMS does not state.

STEP 3 (by 9:00 PM): 30 test offers (task G1), in api/data/offers/
- Files offer01.png to offer30.png, plus answers.json in the same shape as demo_expected.json, written before any run. Add "is_loan_ad": false for the non-loans.
- Cover every case: fee upfront on a short loan (6); plain loan, cheap and dear (5); EMI with the total printed (3); EMI without the total (3); in-hand amount printed (2); days missing (2); an ad whose numbers contradict each other, e.g. loan 5000, fee 1200, "you get 4000" (2); weekly wording ("2 weeks") (2); a blurry or dark phone photo of a printed ad (2); not a loan: a menu, an electricity bill, a shop poster (3).
- For a blurry photo or a contradicting ad, the expected verdict is CANNOT_SAY.

STEP 4 (by 10:00 PM): 10 harassment samples (task G2), in api/data/harassment/samples.json
- Each: {"id": "h01", "at": "2026-11-13T21:40:00+05:30", "channel": "call|sms|whatsapp|telegram|visit", "contacted": "borrower|family|employer|contacts", "text": "...", "expected_rules": ["H1", "H2"]}
- Rules (CLAUDE.md): H1 contact before 08:00 or after 19:00; H2 threats or abuse; H3 contacting family, friends, employer or contacts; H4 public shaming; H5 false claims of arrest, court or police; H6 5 or more calls in one day (make 5 call samples on one date for this).
- Every rule must appear at least once. Include a polite reminder at 11:00 AM that matches NO rule. Mix Hinglish and English. One sample contains an invented 12-digit number (e.g. "Aadhaar 1234 5678 9012") so we can test that the PDF masks it.

STEP 5 (after step 4): RBI directory (task G4)
- RBI publishes a public directory of digital lending apps (DLAs) and the regulated lenders behind them. Find it on rbi.org.in (search the site for "digital lending apps") and download or copy it.
- Save it as api/data/rbi_dla.csv. Keep the header exactly: dla_name,regulated_entity,list_date. Put the date of the list in every row as YYYY-MM-DD.
- In api/data/README.md write the source URL and the date you downloaded it. If you cannot get the full list, copy at least 30 real rows and write that it is partial.

ALSO
- I1, before 7:30 PM: write 3 risky questions to ask the mentor at the review (e.g. "Would a judge trust our cost bands?") and send them to Gurpreet.
- I3, at 7:00 PM: screen-record the rehearsal, a 60-second backup video of photo -> card + voice. Keep it on your laptop; do not commit it.
- Vendor talks, when you can: speak to 2 or 3 street vendors. No names, no phone numbers, no photos of people. Ask: Have you taken a loan from an app? How much did you get in hand? Did you understand the terms? Did agents call you or your family? Would a voice message in Hindi help? Write short notes under "Field notes" in api/data/README.md.

HANDING OVER. One pull request per step. Never push to main and never merge. For each: pull main, make a branch, commit as "data: <what changed>", push, open a pull request, and tell Gurpreet. Do not change any existing file except api/data/rbi_dla.csv and api/data/README.md.
Before each step, tell me in 3 lines what you will make, which files, and how you checked the expected numbers.
```
