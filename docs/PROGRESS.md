# PROGRESS.md: running log (newest entry at the top)

Every agent session and every person adds an entry here at the end of each task, before committing. Never delete or edit someone else's entry. Keep each entry under 12 lines.

## Current status (update this block when a gate passes or the plan changes)
- Now: re-planned at 4:50 PM (D25); no product code yet. Everyone follows docs/PLAN.md: photo or text -> card + Hindi voice, with second reading, merged and tested by 7:00 PM, rehearsal 7:00 to 7:30 PM. Harassment, lender, database and cache wait until after the review.
- Gates: 2:00 PM [x] · 7:30 PM [ ] · 12:30 AM [ ] · 3:30 AM freeze [ ]
- Known broken: (none yet)
- Groq photo reads used today on the server account: 0 of about 80 (Gurpreet's own account: 1)

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
