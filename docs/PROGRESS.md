# PROGRESS.md: running log (newest entry at the top)

Every agent session and every person adds an entry here at the end of each task, before committing. Never delete or edit someone else's entry. Keep each entry under 12 lines.

## Current status (update this block when a gate passes or the plan changes)
- Now (6:30 PM): backend + bot for the review are merged on main (PRs #1 to #11; 152 tests pass): photo or pasted SMS in Telegram -> card + Hindi MP3, second reading on a mismatch. Waiting for: the web /check page (PWA teammate, no PR yet) and the printed ads + SMS offers (data teammate, nothing in api/data yet). Next: real Telegram test on the server laptop, then the 7:00 PM rehearsal. Harassment, lender, database and cache come after the review.
- Gates: 2:00 PM [x] · 7:30 PM [ ] · 12:30 AM [ ] · 3:30 AM freeze [ ]
- Known broken: none in code. Missing for 7:30: printed ads, web /check page, a real Telegram run. Results vanish on API restart (no database yet).
- Groq photo reads used today on the server account: 0 of about 80 (Gurpreet's own account: 6)

## Entry template (copy, fill, paste at the top of the log below)
```
### <time IST> · <task ID(s)> · <person or "agent for <person>">
- Did: <one or two lines>
- Files: <paths>
- Proof: <test command + result, or "tested in Telegram: ...">
- Status in docs/TASKS.md: <review | done>
- Next: <the next step for this area>
- Broken / risks: <anything another person must know, or "none">
```

## Log

### 13 Nov 2026, 7:18 PM · D6 bot side (PR 2 of 4 for D6 + D7) · agent for Siddeshwar
- Did: bot/main.py on_voice: a Telegram voice note goes to POST /api/checks as form field `audio` (voice.ogg), then the same card + MP3 as a photo. Notes over 60 s are refused in Hindi before any Whisper call; a failed download or an unclear note gets "Awaaz saaf nahi aayi. Dobara bolo, ya photo bhejo."; /start mentions voice notes.
- Files: bot/main.py, api/tests/test_bot.py (6 new tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 198 passed. Real run (bot handler + real API + real Whisper / gpt-oss / edge-tts; only Telegram faked): spoken offer -> card ₹5,000 / ₹6,000 / 7 din / ₹1,000 zyada, ⏱ 5.7 sec, then a 64 KB MP3.
- Status in docs/TASKS.md: D6 = review
- Next: D7 (PR 3 server: bn + mr voices; PR 4 bot: /bhasha). Real Telegram voice note with the test bot.
- Broken / risks: not yet tried in the real Telegram app. Stacked on PR 1 (merge #17 first).

### 13 Nov 2026, 7:16 PM · D6 server side (PR 1 of 4 for D6 + D7) · agent for Siddeshwar
- Did: voice note -> card. fallback.transcribe (Groq Whisper, hi, temp 0, timeout, no retries; logs length only). extract.extract_from_voice: Whisper -> gpt-oss "numbers in digits" (D22; raw transcript if it fails) -> code expands "6 हजार" -> 6000 -> extract_from_text. Engines.listen. POST /api/checks takes form field `audio`; no cache, no second reading. Started before the 7:30 gate was confirmed, on Siddeshwar's say-so.
- Files: api/core/fallback.py (transcribe), api/core/extract.py (extract_from_voice, expand_multipliers, MSG_BAD_VOICE), api/core/schemas.py (Engines.listen), api/main.py (create_check audio, run_check audio, engines.listen), api/tests/test_voice.py (new), api/tests/test_pipeline.py (2 expected engines blocks gain "listen": None)
- Proof: `pytest -q` 192 passed (23 new). Real run x3 (edge-tts voice saying "paanch hazaar ka loan, saat din mein chhe hazaar lautana" -> real Whisper + gpt-oss + edge-tts): 5000 / 6000 / 7 din / 1000 extra, VERY_COSTLY, MP3, 5.7 to 9.9 s, 3 of 3 correct.
- Status in docs/TASKS.md: D6 = doing (server side in review; bot side is PR 2)
- Next: PR 2 bot voice handler (bot/main.py), then D7 (PR 3 server, PR 4 /bhasha).
- Broken / risks: real Whisper heard "saath" for "saat" (D22) and the rewrite once left "6 हजार" half-converted; both now handled (prompt examples + code expansion). Voice notes cost 1 Whisper + 2 gpt-oss calls each.

### 13 Nov 2026, 7:05 PM · D6 + D7 handed to Siddeshwar · agent for Gurpreet
- Did: D6 and D7 now belong to Siddeshwar in full (D35), with the exact functions he may change in Gurpreet's files, what his agent must read and check in the installed libraries, specs, tests, and a paste-ready prompt (docs/PLAN.md).
- Files: docs/PLAN.md, docs/TASKS.md, docs/DECISIONS.md (D35), docs/PROGRESS.md
- Proof: docs only.
- Status in docs/TASKS.md: D6, D7 owner = Siddeshwar
- Next: Gurpreet A3 (database). Siddeshwar D6/D7 after the 7:30 gate, then F1, F3, D5.
- Broken / risks: F1, F3, D5 (musts for 12:30 AM) now start later; D6 + D7 first is the lead's call.

### 13 Nov 2026, 7:00 PM · A4 photo cache · agent for Gurpreet
- Did: cache.py stores each photo's CheckResult by SHA-256 of the bytes (one JSON file in CACHE_DIR, written via .part + rename). main.py checks it before any AI call; a hit returns cached=true and the same MP3; a missing MP3 is made again with edge-tts only; check ids continue from the highest id on disk, so a new check never overwrites a cached MP3. Text and not-a-loan answers are not cached.
- Files: api/core/cache.py, api/main.py, api/tests/test_cache.py (new), api/tests/test_pipeline.py, docs/ARCHITECTURE.md, RUNBOOK.md, DEMO.md
- Proof: `pytest -q` 164 passed (12 new). Real: same photo 3 times with an API restart in between -> 1 Qwen call (1.83 s), then 2 cache hits in 0.0 s, MP3 still served after the restart.
- Status in docs/TASKS.md: A4 = review
- Next: A3 database.
- Broken / risks: a cached ad shows "⏱ 0.0 sec" on the card; decide for the demo (DEMO.md checklist).
### 13 Nov 2026, 7:00 PM · seconds stamp on the Telegram card (DEMO LIVE 1) · agent for Gurpreet
- Did: the card ends with "⏱ 3.9 sec" from the API's `seconds`; left out when missing or not a number. One-off edit of Siddeshwar's bot/main.py before he starts D5 (D34).
- Files: bot/main.py, api/tests/test_bot.py, docs/DEMO.md (checklist ticked)
- Proof: `pytest -q` 157 passed (5 new).
- Status in docs/TASKS.md: no task ID (demo fix)
- Next: A4 cache.
- Broken / risks: none.
### 13 Nov 2026, 6:55 PM · after-review split + D7 language change · agent for Gurpreet
- Did: split the remaining backend/bot work between Gurpreet and Siddeshwar by file (PLAN.md "After the review", D34); D7 changed from Kannada to Bengali + Marathi (D32; both edge-tts voices checked to exist); voice-note input contract (D33); signatures for cache, harass, evidence, next_step, transcribe, speak with lang; Siddeshwar's prompt.
- Files: docs/PLAN.md, docs/TASKS.md (D6, D7, owners), docs/DECISIONS.md (D32 to D34), docs/PROGRESS.md
- Proof: docs only; `pytest -q` 152 passed on main.
- Status in docs/TASKS.md: no status change; owners added
- Next: Gurpreet seconds stamp on the card, then A4 (cache); Siddeshwar F1 (harassment rules).
- Broken / risks: Bengali/Marathi sentences need a native speaker's check before D7 is merged.

### 13 Nov 2026, 6:30 PM · docs brought up to date with main · agent for Gurpreet
- Did: all PRs #1 to #11 are merged; local main matches GitHub (7e7b7cb). Updated every doc the code now contradicts: START_HERE (checks are real, merge rules), ARCHITECTURE (what is built, second reading only on a mismatch), TESTING (152 tests, real-run results), RUNBOOK (new symptoms), README, DEMO (seconds stamp, LIVE 2 needs C1/C2), PLAN (status), TASKS (B3, B4, B5, D2 = done after an independent check; D3, D4 review until real Telegram), DECISIONS D28 to D31.
- Files: README.md, docs/START_HERE.md, ARCHITECTURE.md, TESTING.md, RUNBOOK.md, DEMO.md, PLAN.md, TASKS.md, DECISIONS.md, PROGRESS.md
- Proof: `pytest -q` 152 passed on main before this docs-only change.
- Status in docs/TASKS.md: see above
- Next: real Telegram on the server laptop; printed ads from the data teammate; web PRs from the PWA teammate; rehearsal 7:00 PM.
- Broken / risks: no web or data PRs yet (nothing pushed by either Antigravity teammate as of 6:30 PM).

### 13 Nov 2026, 5:50 PM · bot fixes after reviewing PR #7 (D3, D4) · agent for Gurpreet
- Did: on Gurpreet's request, fixed 3 small things in Siddeshwar's bot on a separate branch: the API wait comes from the config timeouts (45 s; the worst photo check needs 36 s, so the bot no longer says "server band hai" while the server is still working); rupees in Indian grouping (₹1,00,000); first bot tests.
- Files: bot/main.py, api/tests/test_bot.py (new)
- Proof: `pytest -q` 152 passed on main + #10 + #7 + this (17 new bot tests). Real API + the bot's own ask_api/send_result (Telegram faked): photo -> card + MP3 3.8 s; SMS 1,00,000 -> ₹95,000 / ₹1,20,000 / 90 din / ₹25,000 + MP3 5.7 s; non-loan -> Hindi refusal only.
- Status in docs/TASKS.md: D3, D4 stay as Siddeshwar set them
- Next: real Telegram test on the server laptop with the demo bot.
- Broken / risks: none.

### 13 Nov 2026, 5:26 PM · D3 D4 (T4) · agent for Siddeshwar
- Did: bot/main.py. Card now HTML (names escaped): verdict line, 4 symbols with bold rupees, RBI line (hidden when lender.match is null, never "illegal"), next step. After the card, the MP3 from audio_url goes by sendAudio; no audio_url or a failed download -> card alone. Pasted text -> POST /api/checks JSON {text, lang "hi", source "telegram"}. 422 -> detail.text_hi; server off / other errors -> Hindi messages.
- Files: bot/main.py, docs/TASKS.md, docs/PROGRESS.md
- Proof: `pytest -q` 6 passed (no bot test file in my list). Handler check script (not committed): 21/21, against the real API app (sample data) and a fake API: card then MP3, card alone, 422 text, server off, JSON body, escaping.
- Status in docs/TASKS.md: D3, D4 = review
- Next: live Telegram run with the test bot once the 6:30 PM merge gives real answers; then "Done when" with the 3 printed ads.
- Broken / risks: not yet run against real Telegram. The Telegram card wording changed (verdict line, RBI line): docs/DEMO.md is the lead's file, please update it.
### 13 Nov 2026, 5:45 PM · L5 second reading (B6) · agent for Gurpreet
- Did: `extract.second_reading`: when cross_check fails on a photo, the OTHER reader (Gemini after Qwen, Qwen after Gemini) reads it again; number fields differing by more than Rs 1, or seen by only one reader, are disputed and set aside before the maths. Other reader down -> the failed sum's fields become unverified. Text never gets a second reading. Only runs on a mismatch (not on every photo).
- Files: api/core/extract.py, api/main.py, api/tests/test_extract.py, api/tests/test_pipeline.py
- Proof: `pytest -q` 131 passed (12 new: invented in_hand caught, agreed within Rs 1, Gemini-first asks Qwen, disagreeing repay, reader down, self-contradicting ad, text). Real run: synthetic ad "loan 5000, fee 1200, you get 4000" -> Qwen 2.08 s, mismatch, Gemini 3.51 s agrees -> CANNOT_SAY, in-hand unverified, "saaf nahi padhe gaye" voice, 7.5 s total.
- Status in docs/TASKS.md: B6 = review
- Next: rehearsal prep: server laptop, demo bot, printed ads (data teammate), bot PR #7 against the real API.
- Broken / risks: none new. Merge order for Gurpreet: #2, #5, #8, #3, #4, #6, #9, #10, then #7.

### 13 Nov 2026, 5:55 PM · L4 join the parts in POST /api/checks (A7) · agent for Gurpreet
- Did: POST /api/checks is real: photo or text -> extract -> cross_check -> fill_gaps -> compute -> decide -> speech_text -> make_audio; results kept in memory; GET /api/checks, /api/checks/{id}, /api/audio/{id}.mp3 and /api/stats read them. No card -> 422 {code, text_hi} (D26). lender.match is null. Form text (urlencoded) accepted too. Merged Siddeshwar's maths, verdict and speak branches into this branch to wire against them.
- Files: api/main.py, api/core/schemas.py (lender.match nullable), api/tests/test_pipeline.py (new), api/tests/test_smoke.py
- Proof: `pytest -q` 119 passed (14 new pipeline tests). Real server: ad photo -> 3800/5000/7/1200, VERY_COSTLY, MP3, 3.9 s; Hinglish SMS -> 9000/11500/14/2500, VERY_COSTLY, MP3, 4.7 s (checked by hand); non-loan -> 422 Hindi.
- Status in docs/TASKS.md: A7 = review
- Next: L5 second reading; then Siddeshwar's bot (#7) against the real API.
- Broken / risks: results vanish on restart (no database until A3). Cases, PDF, verify are still sample data.

### 13 Nov 2026, 5:45 PM · L3 extract.py (B1, B2, B7, B8) · agent for Gurpreet
- Did: reading prompt; strip fences; Pydantic `Fields` that turns "Rs 5,000" -> 5000, "2 weeks" -> 14 days, "10%" fee -> rupees (in code); not-a-loan and nothing-readable raise NotALoan / Unreadable with the Hindi text; SMS numbers not written in the message are dropped (stops invented in_hand, D18); regex backup when gpt-oss is down or answers badly.
- Files: api/core/extract.py, api/tests/test_extract.py (new)
- Proof: `pytest -q` 59 passed (40 new; uses the real Qwen/Gemini replies). Real run: ad photo via Qwen 2.18 s -> 5000/1200/5000/7; English and Hinglish SMS via gpt-oss ~1 s, both correct; a non-loan message -> polite Hindi refusal.
- Status in docs/TASKS.md: B2, B7, B8 = review; B1 = review on the synthetic ad, the 3 printed ads still to test
- Next: L4 join everything in POST /api/checks (needs Siddeshwar's PRs #3, #4 and speak.py).
- Broken / risks: B1 "done when" needs the printed ads (data teammate, 6:00 PM). Second reading (L5) not in yet.

### 13 Nov 2026, 5:40 PM · L2 read_image(), read_text() (A4, A6) · agent for Gurpreet
- Did: Qwen -> Gemini photo reading, gpt-oss-20b text reading. Each engine once, temperature 0, timeout from config, Groq max_retries=0, Gemini 1 attempt; a 429, error or a reply that `check` rejects moves on at once; EngineError when all fail. Logs engine, seconds, tokens, Groq tokens/requests left; errors logged by type + status only.
- Files: api/core/fallback.py, api/tests/test_fallback.py, docs/PLAN.md (read_image now takes `prompt` and `check`)
- Proof: `pytest -q` 19 passed (8 new). Real run on a synthetic ad: Qwen 1.17 s (1,866 prompt tokens), Gemini 4.54 s, gpt-oss-20b 0.80 s; all three read 5000 / 1200 / 5000 / 7 correctly.
- Status in docs/TASKS.md: A4 = doing (cache after the review); A6 = review (engine + seconds returned by every read)
- Next: L3 extract.py (prompt, number clean-up, Pydantic, not-a-loan, regex backup).
- Broken / risks: readers return numbers as text ("Rs 5000", "7 days"); extract.py must convert them. Qwen put the app name in lender_name too.

### 13 Nov 2026, 5:20 PM · L1 speak() (part of A4) · agent for Gurpreet
- Did: `fallback.speak(text, out_path) -> bool`: edge-tts hi-IN-SwaraNeural, timeout from config, writes a .part file then renames, never raises (False = send the card alone). Added `EngineError` and the agreed `read_image` / `read_text` signatures (still stubs).
- Files: api/core/fallback.py, api/tests/test_fallback.py (new)
- Proof: `pytest -q` 11 passed (5 new: ok, no internet, timeout, empty audio, empty text). Real run: sample sentence -> 72 KB MP3 in 3.05 s and 1.51 s.
- Status in docs/TASKS.md: A4 = doing (Gurpreet); speak part ready for Siddeshwar's make_audio (T3)
- Next: L2 `read_image()` (Qwen -> Gemini) and `read_text()` (gpt-oss-20b).
- Broken / risks: speak needs internet; the venue network is untested.
### 13 Nov 2026, 5:08 PM · B3 B4 (T1) · agent for Siddeshwar
- Did: maths.py to docs/PLAN.md "Rules inside the maths": cross_check, fill_gaps(fields, disputed), compute. Whole numbers round half up. A sum cross_check still finds broken is treated as disputed (safety net). A fee that was printed but disputed is not treated as "no fee": in_hand stays unverified.
- Files: api/core/maths.py, api/tests/test_maths.py, docs/TASKS.md, docs/PROGRESS.md
- Proof: `pytest -q` 25 passed (19 maths: PLAN.md rows 1-10 + cross-check + safety cases; 6 smoke).
- Status in docs/TASKS.md: B3, B4 = review
- Next: T2 verdict.py (B5), then T3 speak.py (D2), T4 bot (D3, D4).
- Broken / risks: none known. maths.py is not called by api/main.py until the lead's 6:30 PM merge.
### 13 Nov 2026, 5:12 PM · B5 (T2) · agent for Siddeshwar
- Did: verdict.py decide(numbers, fees) per docs/PLAN.md: CANNOT_SAY if in_hand, repay_total, tenure_days or apr_simple is unverified; VERY_COSTLY if apr > 100 or a fee on a loan of 30 days or less; COSTLY if apr >= 36; else USUAL. Thresholds are read from config.settings on every call.
- Files: api/core/verdict.py, api/tests/test_verdict.py, docs/TASKS.md, docs/PROGRESS.md
- Proof: `pytest -q` 23 passed (17 verdict: PLAN.md rows 1-10, edges 35/36/100/101, fee rule at 30 vs 31 days, band_costly_apr 20 turns row 2 COSTLY; 6 smoke).
- Status in docs/TASKS.md: B5 = review
- Next: T3 speak.py (D2).
- Broken / risks: none known. The skeleton's decide(numbers) gained the fees argument, as agreed in docs/PLAN.md.
### 13 Nov 2026, 5:23 PM · D2 (T3) · agent for Siddeshwar
- Did: speak.py. speech_text fills the fixed Hindi sentence from CLAUDE.md (whole numbers, no commas), or says "Is offer ke saare number saaf nahi padhe gaye..." when in_hand, repay_total, tenure_days or extra is unverified. make_audio writes <AUDIO_DIR>/<id>.mp3 through fallback.speak and returns /api/audio/<id>.mp3, or None when voice is off, fails or raises.
- Files: api/core/speak.py, api/tests/test_speak.py, docs/TASKS.md, docs/PROGRESS.md
- Proof: `pytest -q` 19 passed (13 speak with a fake fallback.speak: PLAN.md row 1 sentence exact, row 8 "not clear", audio ok / failed / error / voice off; 6 smoke).
- Status in docs/TASKS.md: D2 = review
- Next: T4 bot (D3, D4).
- Broken / risks: a real edge-tts run from this laptop's Claude session timed out at 6 s (connection never opened; probably the session sandbox, not yet re-tried outside it). "MP3 in under 5 s" is not proven yet: check it once fallback/speak is merged.

### 13 Nov 2026, 5:15 PM · teammate prompts + PR workflow · agent for Gurpreet
- Did: full paste-ready prompts in docs/PLAN.md for Siddeshwar (Claude Code), the PWA teammate (RajuCard, /check, errors, Raju mode, home-screen app) and the data teammate (demo ads, SMS offers, 30 offers, harassment samples, RBI list, vendor notes). Every change now goes through a PR; Gurpreet merges (D27).
- Files: docs/PLAN.md, docs/TASKS.md (E6 into tonight; G1, G2, I1, I3 to the data teammate), docs/DECISIONS.md (D27), docs/PROGRESS.md
- Proof: `pytest -q` (see the PR); docs only.
- Status in docs/TASKS.md: no status change
- Next: Gurpreet merges this PR and sends the prompts; then L1 (`speak()` in fallback.py, task A4).
- Broken / risks: started 20 minutes behind the 5:00 PM plan; my 5:25 and 5:45 targets will slip to about 5:45 and 6:05.

### 13 Nov 2026, 5:05 PM · re-plan for the 7:30 PM review · agent for lead
- Did: wrote docs/PLAN.md: goal, who owns which files, order with target times, agreed signatures, 6:30 PM merge point, hand-worked test values, rehearsal checklist, and a paste-ready prompt for each teammate. Docs only.
- Files: docs/PLAN.md (new), docs/TASKS.md (new tasks A7, B8, E9, G8; D1 = review), docs/DECISIONS.md (D25, D26), docs/PROGRESS.md
- Proof: `pytest -q` 6 passed (still the sample-data smoke tests; nothing real is built).
- Status in docs/TASKS.md: D1 = review (the lead's 2:00 PM gate test); everything else in scope is todo
- Next: lead starts L1 (`speak()` in fallback.py); teammate starts T1 (maths.py). Merge point 6:30 PM, hard stop 7:00 PM.
- Broken / risks: 2 hours for the whole pipeline; second reading is last in the lead's order so it is the first thing to slip. `lender.match` becomes nullable (D26), a small contract change. Printed ads are needed by 6:00 PM to test real phone photos.

### 13 Nov 2026, 3:10 PM · 2:00 PM gate · agent for lead
- Did: logged the lead's gate test and the work split (D24). Docs only, no product code.
- Files: docs/PROGRESS.md, docs/DECISIONS.md
- Proof: tested by the lead: a photo in Telegram returned the text card and /check showed the sample data.
- Status in docs/TASKS.md: no change
- Next: 7:30 PM gate: 3 printed ads photographed in Telegram -> Hindi voice + card, twice in a row.
- Broken / risks: the reply is still sample data (no real reading, maths or audio yet); api/data/rbi_dla.csv has only its header row; no printed ads or test offers in the repo yet.

### 13 Nov 2026, 1:30 PM · A1 A2 E1 scaffold (+ D1 skeleton) · agent for lead
- Did: starter repo. Every API route returns sample data; bot sends a photo to the API and replies with the text card; web has 4 routes, top bar, light/dark toggle, and /check shows the sample check from the API. Other api/core files are skeletons that name their task.
- Files: api/, bot/, web/, scripts/, docs/START_HERE.md, .gitignore, .gitattributes, .editorconfig, pytest.ini
- Proof: fresh venv `pip install -r api/requirements.txt` OK · `pytest -q` 6 passed · curl /api/health and POST /api/checks return JSON · `npm ci && npm run build` OK · all 4 web routes render in light and dark with no console errors · `import bot.main` OK · secret scan clean
- Status in docs/TASKS.md: A1, A2, E1 = review; D1 = todo (skeleton only)
- Next: lead pushes to GitHub; everyone clones and runs scripts/setup; then A3 (db), A4 (fallback + cache), B1 (extract), B3 (maths).
- Broken / risks: the bot was NOT tested against real Telegram here (no token in the build sandbox): test it first. Audio and PDF routes return 404 until D2 and F3. shadcn installed its newer "base-nova" style (Base UI under the hood).

### 13 Nov 2026, before 11:30 AM · prep · lead
- Did: created Telegram demo + test bots, Gemini and Groq keys; ran prep/test_keys.py and prep/tg_test.py.
- Files: prep/ (not in this repo); results in docs/PREP.md.
- Proof: test_keys 7/9 PASS (Gemini 3.8 Flash and Gemma 503, both dropped); tg_test PASS (photo in, text + MP3 out).
- Status in docs/TASKS.md: n/a
- Next: A1 repo setup at 11:30 AM.
- Broken / risks: Groq allows about 80 photo reads/day per account; use your own keys while building.
