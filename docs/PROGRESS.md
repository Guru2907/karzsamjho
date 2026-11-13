# PROGRESS.md: running log (newest entry at the top)

Every agent session and every person adds an entry here at the end of each task, before committing. Never delete or edit someone else's entry. Keep each entry under 12 lines.

## Current status (update this block when a gate passes or the plan changes)
- Now (9:00 PM): the 7:30 PM review passed. On main (23 PRs, 266 tests): photo / SMS / Hindi voice note -> card + voice in hi / bn / mr, second reading, cache, advance-fee warning, lakh/crore. Night plan with owners and prompts: docs/PLAN.md "Night plan" (D37 mentor feedback, D38 owners, D39 WhatsApp). Critical path: A3 -> F2 -> F3/F4 -> D5 and G4 -> C1 -> C2/C4/F5.
- Gates: 2:00 PM [x] · 7:30 PM [x] (review passed) · 12:30 AM [ ] · 3:30 AM freeze [ ]
- Known broken: none in code. Missing: web pages (Tejaswini, no PR yet), RBI CSV (Anam), database, lender check, harassment log. bn/mr sentences await the native-speaker OK.
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

### 14 Nov 2026, 12:05 AM · B9b scam rule in more scripts · agent for Gurpreet
- Did: the advance-fee code rule (backup for the AI) now knows Devanagari Hindi, Bengali and Marathi pay / charge / before words, matched as plain text because their vowel signs break ; sentences also split on । and ॥. Left out on purpose: Bengali দিন ("give" and "day") and कर ("tax", but inside कर्ज). English words keep matching with endings (released, disbursal).
- Files: api/core/extract.py, api/tests/test_advance_fee.py, docs/ARCHITECTURE.md, TASKS.md
- Proof: `pytest -q` 280 passed (14 new: 6 scams caught, 6 normal offers / repayments not, । split, Devanagari voice note caught when the AI misses it). Real AI: hi / bn / mr scams -> 1500 / 1200 / 1500 from both the AI and the code rule; normal Marathi offer -> no warning, numbers right.
- Status in docs/TASKS.md: B9b = review
- Next: C1 lender check (needs Anam's RBI CSV, G4).
- Broken / risks: none.
### 14 Nov 2026, 12:45 AM · B11 Gemini backup for SMS and voice · agent for Gurpreet
- Did: read_text tries gpt-oss-20b then Gemini Flash-Lite (regex stays the caller's last resort); transcribe tries Whisper then Gemini listening to the audio (OGG / WAV / MP3). Same rules: temperature 0, timeout, no retry, a 429 or a rejected reply moves on, engine name recorded. Harassment labelling (F1) gets the backup too because it uses read_text. Tests: conftest makes both Gemini backups offline, so no test reaches the internet even with real keys.
- Bug found in the first drill and fixed: the Gemini client was not kept in a variable, so Python closed it before the request ("client has been closed"); a regression test fails if that comes back.
- Files: api/core/fallback.py, api/tests/test_fallback.py, api/tests/conftest.py, docs/ARCHITECTURE.md, TASKS.md
- Proof: `pytest -q` 281 passed (15 new), also with real keys loaded (1.4 s, no network). Real drill with a wrong Groq key: Hinglish SMS -> read by Gemini -> 9000 / 11500 / 14 / 2500 in 4.1 s; Hindi voice note -> heard and read by Gemini -> 5000 / 6000 / 7 / 1000 in 8.1 s.
- Status in docs/TASKS.md: B11 = review
- Next: wave 1 is done. Later list: C2, F4, F5, G6, G7 (kill-switch drill), G5, I5.
- Broken / risks: Gemini free tier is 15/min, 500/day, shared by photos, SMS and voice when Groq is down.
### 14 Nov 2026, 12:20 AM · C1 RBI lender check · agent for Gurpreet
- Did: lender.py matches the app/lender name read from the ad (RapidFuzz WRatio; generic words like loan/app/pvt/ltd stripped, better score kept; also against the regulated entity) and any website / Play Store link in the SMS against the local copy of RBI's directory (api/data/rbi_dla.csv, path in config RBI_DLA_PATH; re-read when the file changes). FOUND >= 90 / SIMILAR >= 70 / NOT_FOUND; a listed name with a link to another domain = SIMILAR (possible clone); empty directory or nothing read = null ("not checked", never "not found"). main.py fills CheckResult.lender and adds Siddeshwar's spoken line (C4) when his function is present.
- Files: api/core/lender.py, api/core/config.py, api/main.py, api/tests/test_lender.py (new), docs/ARCHITECTURE.md, TASKS.md
- Proof: `pytest -q` 282 passed (16 new, made-up directory only). With C4 (#28) merged in a throwaway copy: 341 passed. Real AI + made-up directory: listed app + link -> FOUND, voice "RBI ki list mein hai, ... se juda hai"; same name, other link -> SIMILAR; "CashNow" vs "CashNow24" -> SIMILAR; unlisted -> NOT_FOUND "RBI ki list mein nahi mila".
- Status in docs/TASKS.md: C1 = review
- Next: fix the advance-fee false positive found in this run (see risks); then A5, B11.
- Broken / risks: api/data/rbi_dla.csv is still only the header (Anam's G4), so on main every check stays "not checked". FOUND in this run's first SMS also showed a B9 bug: the AI marked "Loan Rs 5000 approved. Fee Rs 500" as pay-first, the fee was dropped and in-hand showed 5000 instead of 4500 (K risk). Fix proposed as the next task.
### 14 Nov 2026, 12:35 AM · evidence PDF route connected (F3 wiring) · agent for Gurpreet
- Did: found in the 11-PR merge check: Siddeshwar's build_pdf (F3) and his bot's PDF download (D5) were done, but /api/cases/{id}/evidence.pdf in main.py still answered 404. It now builds the PDF fresh from the database (with the day counter) and returns application/pdf. The fingerprint formula in evidence.py and main.py was checked to be identical.
- Files: api/main.py, api/tests/test_cases.py
- Proof: `pytest -q` 377 passed (2 new: real %PDF, every event, 12-digit number masked). Real: case with a 9:40 PM threat + Aadhaar 1234 5678 9012 and a message to the son -> PDF with H1, H2, H3, the timeline, "XXXX XXXX 9012", the hash chain, where to complain and a complaint draft.
- Status in docs/TASKS.md: no own task ID (connects F3 to the API)
- Next: F4 verify (the PDF says /verify checks the chain, but it still always answers ok).
- Broken / risks: built on #35 (+ #26, #29) with #30 merged in: merge after #30 and #35.

### 14 Nov 2026, 12:35 AM · A5 health: engines up or down · agent for Gurpreet
- Did: fallback.ping() checks Groq (model list), Gemini (model lookup) and edge-tts (voice list) in parallel: free calls, no loan reads, 4 s timeout, cached 60 s (`?fresh=true` re-checks). /api/health adds engines up/down with the reason, can_read_photos, can_speak and the database state; it still answers if the database is broken; keys only as set / not set. Stats come from the database (A3); a test checks they match. Tests never ping the internet (conftest.py).
- Files: api/core/fallback.py, api/main.py, api/tests/test_health.py (new), api/tests/conftest.py, docs/RUNBOOK.md, TASKS.md
- Proof: `pytest -q` 283 passed (9 new). Real: all three engines UP (0.6 to 1.0 s); with a deliberately wrong Groq key -> groq DOWN (AuthenticationError 401), gemini UP, can_read_photos true.
- Status in docs/TASKS.md: A5 = review
- Next: B11 (Gemini backup for SMS and voice).
- Broken / risks: built on #26 (A3): merge after it.
### 13 Nov 2026, 11:57 PM · D5 bot harassment log · agent for Siddeshwar
- Did: bot/main.py: a forwarded text message, or a message after /log (or /log <words>), becomes an event: POST /api/cases once per chat (id kept in chat_data; the case names the lender of his last check), POST /api/cases/{id}/events with at = the ORIGINAL message time in IST, channel telegram, contacted borrower; then a Hindi line with the rules broken, then GET evidence.pdf sent with reply_document. /pdf sends it again. A case lost on a server restart is made again once. Hindi messages only.
- Files: bot/main.py, api/tests/test_bot.py (12 new tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 360 passed (the fake API serves the real F3 PDF). Real run against the API on main (sample cases): case_0007 remembered, "Darj ho gaya ... H1 raat ya subah jaldi sampark", then the Hindi "PDF abhi nahi ban paya, /pdf bhejo" because the PDF endpoint is not real yet.
- Status in docs/TASKS.md: D5 = review
- Next: once F2 + the evidence.pdf endpoint land, a real Telegram run (forward a threat, get the PDF). Then stretch D9, D10, D8.
- Broken / risks: a forwarded TEXT is always treated as harassment (a forwarded loan SMS too); paste a loan SMS instead of forwarding it. docs/DEMO.md (Gurpreet) may need the new /log, /pdf flow.

### 13 Nov 2026, 11:53 PM · F3 evidence PDF · agent for Siddeshwar
- Did: evidence.build_pdf(case) -> English PDF: case details + "Day N of 30", rules-broken table with the RBI basis (H6 marked as our threshold), timeline (masked words), every hash and prev_hash, where to complain (case route, or all routes + police when H2/H5), complaint draft on one page. mask(): any 12-digit number -> "XXXX XXXX 1234". Text in Devanagari/Bengali script gets a note instead of broken letters (D20). Also event_hash / verify_chain = SHA-256(prev_hash + event fields) for F2 / F4 if Gurpreet wants one shared definition.
- Files: api/core/evidence.py, api/tests/test_evidence.py (new, 23 tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 348 passed. Sample PDF checked by eye: 2 pages, every section present, Aadhaar masked.
- Status in docs/TASKS.md: F3 = review
- Next: D5 bot (forward -> case event -> PDF).
- Broken / risks: GET /api/cases/{id}/evidence.pdf is Gurpreet's main.py: it should return build_pdf(case) with media_type application/pdf. Needs F2 for real cases.

### 13 Nov 2026, 11:48 PM · C4 spoken lender result · agent for Siddeshwar
- Did: speak.lender_sentence(lender, lang) -> fixed sentence for FOUND / SIMILAR / NOT_FOUND, None when match is null (D37, mentor feedback: Raju cannot read the card). Hindi exactly as docs/PLAN.md "Night plan"; bn / mr are drafts waiting for the native-speaker OK. Never "safe", "illegal" or "fake" (tested in all three languages).
- Files: api/core/speak.py, api/tests/test_speak.py (14 new tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 325 passed.
- Status in docs/TASKS.md: C4 = review (wiring into the voice is Gurpreet's main.py, after C1)
- Next: F3 evidence PDF, then D5.
- Broken / risks: not spoken yet: main.py must append lender_sentence(...) after speech_text(...) once C1 fills lender.match. bn / mr wording needs a native speaker.
### 13 Nov 2026, 11:55 PM · F2 cases, events, hash chain · agent for Gurpreet
- Did: /api/cases, /api/cases/{id} and POST /api/cases/{id}/events are real (A3 database, sample data removed). Each event: time normalised to IST, rules from Siddeshwar's harass.label (calls that day INCLUDING this one, for H6), hash = SHA-256(prev_hash + compact sorted JSON of at/channel/contacted/text/rules), first prev_hash = 64 zeros; one lock so the chain never forks. If harass.label is missing or fails, the event is still stored with no rules. Day counter (day 1 = opening day, IST). `event_hash` is shared with F4.
- Files: api/main.py, api/tests/test_cases.py (new), api/tests/test_smoke.py, docs/ARCHITECTURE.md, TASKS.md
- Proof: `pytest -q` 283 passed (9 new); with Siddeshwar's F1 (#27) merged in a throwaway copy: 328 passed. Real run with F1 + real AI: night threat -> H1 H2; message to the son -> H3; polite 11:30 AM reminder -> none; 5th call in a day -> H6; API restarted -> 8 events, every link and every hash recomputes.
- Status in docs/TASKS.md: F2 = review
- Next: B9b, then C1. Siddeshwar's F3 (PDF) and D5 (bot) can now build on these routes.
- Broken / risks: verify (F4) still answers ok=true for everything until F4. Merge order: #26 (A3) -> #27 (F1) -> this.

### 13 Nov 2026, 11:46 PM · F1 harassment rules · agent for Siddeshwar
- Did: harass.label(event, calls_that_day) -> sorted rule ids. H1 (before 08:00 / after 19:00 IST, hours from config), H6 (calls_that_day >= h6_calls_per_day, "our threshold") and H3 when contacted is family/employer/contacts are plain code. H2-H5: gpt-oss-20b JSON (check= parser) plus a Hinglish/English/Devanagari keyword list, used alone when the model is down and added as a safety net when it answers. RULES (English meanings) and RULES_BASIS for the PDF.
- Files: api/core/harass.py, api/tests/test_harass.py (new, 45 tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 311 passed. Real gpt-oss on 10 hand-written samples: 10/10 match (first try without the safety net: 7/10; it missed "family ko sab bata diya" H3 and "warna police" H2). Polite 11 AM reminder -> []. ~2 s per event.
- Status in docs/TASKS.md: F1 = review
- Next: C4 lender sentence, then F3 PDF, then D5 bot.
- Broken / risks: the old skeleton name label_event is replaced by label (docs/PLAN.md signature). No G2 samples in api/data/harassment yet, so the samples are in the test file.
### 13 Nov 2026, 11:45 PM · A3 SQLite database · agent for Gurpreet
- Did: db.py stores checks, cases and events in SQLite (DB_PATH, *.db not committed); one short connection per call; helpers for F2: last_event_hash (chain start = 64 zeros) and calls_on (H6). main.py writes every check to the database (cache hits never overwrite the first answer), reads /api/checks, /api/checks/{id} and /api/stats from it, keeps CHECKS only as a fast in-memory copy, and never reuses a check id after a restart. Every test now gets its own temp database (conftest.py). /api/cases is still sample data until F2.
- Files: api/core/db.py, api/main.py, api/tests/test_db.py (new), api/tests/conftest.py, docs/ARCHITECTURE.md, START_HERE.md, RUNBOOK.md, TASKS.md
- Proof: `pytest -q` 274 passed (8 new), no real database file created by the tests. Real: SMS check chk_0001 (4500 / 5600 / 7 / 1100) -> API fully stopped -> started again -> same check returned from the database; stats and health count it.
- Status in docs/TASKS.md: A3 = review
- Next: F2 events + hash chain (unblocks Siddeshwar's F3 and D5).
- Broken / risks: none. Before the demo, copy karzsamjho.db with cache/ and audio/ to the backup laptop (RUNBOOK).
### 13 Nov 2026, 11:53 PM · F3 evidence PDF · agent for Siddeshwar
- Did: evidence.build_pdf(case) -> English PDF: case details + "Day N of 30", rules-broken table with the RBI basis (H6 marked as our threshold), timeline (masked words), every hash and prev_hash, where to complain (case route, or all routes + police when H2/H5), complaint draft on one page. mask(): any 12-digit number -> "XXXX XXXX 1234". Text in Devanagari/Bengali script gets a note instead of broken letters (D20). Also event_hash / verify_chain = SHA-256(prev_hash + event fields) for F2 / F4 if Gurpreet wants one shared definition.
- Files: api/core/evidence.py, api/tests/test_evidence.py (new, 23 tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 348 passed. Sample PDF checked by eye: 2 pages, every section present, Aadhaar masked.
- Status in docs/TASKS.md: F3 = review
- Next: D5 bot (forward -> case event -> PDF).
- Broken / risks: GET /api/cases/{id}/evidence.pdf is Gurpreet's main.py: it should return build_pdf(case) with media_type application/pdf. Needs F2 for real cases.

### 13 Nov 2026, 11:48 PM · C4 spoken lender result · agent for Siddeshwar
- Did: speak.lender_sentence(lender, lang) -> fixed sentence for FOUND / SIMILAR / NOT_FOUND, None when match is null (D37, mentor feedback: Raju cannot read the card). Hindi exactly as docs/PLAN.md "Night plan"; bn / mr are drafts waiting for the native-speaker OK. Never "safe", "illegal" or "fake" (tested in all three languages).
- Files: api/core/speak.py, api/tests/test_speak.py (14 new tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 325 passed.
- Status in docs/TASKS.md: C4 = review (wiring into the voice is Gurpreet's main.py, after C1)
- Next: F3 evidence PDF, then D5.
- Broken / risks: not spoken yet: main.py must append lender_sentence(...) after speech_text(...) once C1 fills lender.match. bn / mr wording needs a native speaker.

### 13 Nov 2026, 11:46 PM · F1 harassment rules · agent for Siddeshwar
- Did: harass.label(event, calls_that_day) -> sorted rule ids. H1 (before 08:00 / after 19:00 IST, hours from config), H6 (calls_that_day >= h6_calls_per_day, "our threshold") and H3 when contacted is family/employer/contacts are plain code. H2-H5: gpt-oss-20b JSON (check= parser) plus a Hinglish/English/Devanagari keyword list, used alone when the model is down and added as a safety net when it answers. RULES (English meanings) and RULES_BASIS for the PDF.
- Files: api/core/harass.py, api/tests/test_harass.py (new, 45 tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 311 passed. Real gpt-oss on 10 hand-written samples: 10/10 match (first try without the safety net: 7/10; it missed "family ko sab bata diya" H3 and "warna police" H2). Polite 11 AM reminder -> []. ~2 s per event.
- Status in docs/TASKS.md: F1 = review
- Next: C4 lender sentence, then F3 PDF, then D5 bot.
- Broken / risks: the old skeleton name label_event is replaced by label (docs/PLAN.md signature). No G2 samples in api/data/harassment yet, so the samples are in the test file.

### 13 Nov 2026, 9:15 PM · WhatsApp skipped · agent for Gurpreet
- Did: the lead skipped WhatsApp: D41 reverses D39, D12 dropped, CLAUDE.md and AGENTS.md list WhatsApp as plain out of scope again; removed from Siddeshwar's prompt.
- Files: CLAUDE.md, AGENTS.md, docs/PLAN.md, TASKS.md, DECISIONS.md (D41), PROGRESS.md
- Proof: docs only.
- Status in docs/TASKS.md: D12 = dropped
- Next: wave 1 (D40).
- Broken / risks: none.

### 13 Nov 2026, 9:00 PM · 7:30 PM gate passed + night plan · agent for Gurpreet
- Did: ticked the 7:30 PM gate (the review passed); recorded the mentor's feedback (D37: lender check by name + website, spoken, never "safe"); night owners by group exactly as the lead assigned (D38); WhatsApp only as stretch-of-stretch D12 (D39); new tasks C4, D8 to D12; owners on every open task; prompts for Gurpreet, Siddeshwar, Tejaswini and Anam in docs/PLAN.md "Night plan"; stale lines fixed (test counts, ARCHITECTURE, DEMO LIVE 2, CLAUDE.md/AGENTS.md WhatsApp note).
- Files: CLAUDE.md, AGENTS.md, docs/PLAN.md, TASKS.md, DECISIONS.md, PROGRESS.md, ARCHITECTURE.md, TESTING.md, START_HERE.md, DEMO.md
- Proof: docs only; `pytest -q` 266 passed on main (611cb0a).
- Status in docs/TASKS.md: owners on every open task
- Next (D40 wave 1): Gurpreet B9b, A3, F2, C1, A5, B11; Siddeshwar F1, C4, F3, D5 then D9, D10, D8, D11; Anam G4, G2, G8, G3; Tejaswini E2/E3/E9, E6, E4/E5, E8, E7.
- Broken / risks: no web PR yet; the RBI CSV blocks C1, C2, F5; A3 blocks F2 and the rest of feature 4.

### 13 Nov 2026, 7:50 PM · B9 warning in Bengali and Marathi · agent for Gurpreet
- Did: the "Savdhaan!" advance-fee warning was Hinglish only, so with /bhasha set to Bengali or Marathi that voice read Hindi words with a Bengali/Marathi accent (found in Gurpreet's live test). Now the warning is in the voice's own language and script (drafts, need the native-speaker OK like D32).
- Files: api/main.py, api/tests/test_advance_fee.py
- Proof: `pytest -q` 266 passed (3 new: hi / bn / mr warning; no "Savdhaan" in bn/mr). Sample MP3s made for the native check.
- Status in docs/TASKS.md: B9 stays review
- Next: native speakers approve the bn/mr sentences and warnings.
- Broken / risks: voice-note INPUT is still Hindi only (Whisper language "hi"); Bengali speech is not understood.

### 13 Nov 2026, 7:24 PM · D7 bot side (PR 4 of 4 for D6 + D7) · agent for Siddeshwar
- Did: bot/main.py /bhasha: three inline buttons (Hindi, বাংলা, मराठी), the choice kept in context.chat_data["lang"] and sent as `lang` with every photo, pasted SMS and voice note; default Hindi. Card text stays Hinglish. /start mentions /bhasha.
- Files: bot/main.py, api/tests/test_bot.py (11 new tests), docs/PROGRESS.md, docs/TASKS.md
- Proof: `pytest -q` 231 passed. Real run (bot handlers + real API, Telegram faked): press বাংলা -> "Theek hai: ab awaaz Bangla (বাংলা) mein aayegi."; ad photo -> Hinglish card ₹3,800 / ₹5,000 / 7 din / ₹1,200 + Bengali MP3 (from the bn cache, 0.0 s).
- Status in docs/TASKS.md: D7 = review (merge only after native-speaker approval)
- Next: native speakers approve; real Telegram run with the test bot (voice note + /bhasha); then F1, F3, D5.
- Broken / risks: the language choice lives in the bot's memory, so it resets to Hindi when the bot restarts. Stacked on #20 (merge #17, #18, #20 first).

### 13 Nov 2026, 7:22 PM · D7 server side (PR 3 of 4 for D6 + D7) · agent for Siddeshwar
- Did: Bengali + Marathi voice. config: tts_voice_bn / tts_voice_mr + tts_voice(lang) and LANGS; .env.example TTS_VOICE_BN / TTS_VOICE_MR. fallback.speak(voice=None). speak.speech_text(numbers, lang) with the bn / mr sentences copied from docs/PLAN.md; make_audio(check_id, text, lang). cache.image_key(image, lang): Hindi key unchanged, bn / mr differ. main: lang read from form or JSON (hi / bn / mr, else hi) and passed to the cache key, speech_text, make_audio and _from_cache (one extra argument there, so a cached bn photo is never re-voiced in Hindi).
- Files: api/core/config.py, .env.example, api/core/fallback.py (speak), api/core/speak.py, api/core/cache.py (image_key), api/main.py (_lang, _from_cache lang, run_check lang, create_check), api/tests/test_lang.py (new, 22 tests)
- Proof: `pytest -q` 220 passed. Real run: synthetic ad -> real Qwen -> 3800 / 5000 / 7 / 1200 VERY_COSTLY; lang bn -> bn-IN-TanishaaNeural MP3 (6.0 s), lang mr -> mr-IN-AarohiNeural MP3 (5.0 s). Whisper listen-back: bn numbers all correct (as words); mr 3800 and 1200 correct, "7 दिवसांत 5000" came back garbled.
- Status in docs/TASKS.md: D7 = doing (server side in review; waiting for native-speaker approval; bot /bhasha next)
- Next: a Bengali and a Marathi speaker listen to both MP3s and approve the sentences; PR 4 /bhasha in the bot.
- Broken / risks: DO NOT MERGE before native-speaker approval (D32). The Marathi "7 दिवसांत 5000" part needs a human ear. _from_cache is outside the D35 list (one argument).

### 13 Nov 2026, 7:35 PM · B9 advance-fee warning + B10 lakh/crore · agent for Gurpreet
- Did: the reader also copies `pay_first` (money asked before the loan); a code rule backs it up for SMS; such a check gets next step DO_NOT_PAY_FIRST and the voice starts "Savdhaan! ... Paise mat bhejo"; a pay-first scam with no loan numbers now answers instead of "samajh nahi aaya". "5 lakh", "2 crore", "50 hazaar", "5k" become rupees (AI path, regex path, and the invented-number check). CLAUDE.md reader field list updated (D36).
- Files: api/core/extract.py, api/main.py, api/tests/test_advance_fee.py (new), CLAUDE.md, docs/TASKS.md (B9, B10 new), DECISIONS.md (D36), ARCHITECTURE.md, TESTING.md, DEMO.md
- Proof: `pytest -q` 224 passed (32 new). Real API + gpt-oss on Anam's 3 scam texts: scam2 and scam3 warned, scam1 not, "₹5 lakh" -> 500000; a normal offer unchanged.
- Status in docs/TASKS.md: B9, B10 = review
- Next: A3 database.
- Broken / risks: api/data/offers/sms_offers.json (Anam's, #19) expects scam3 in_hand 498800; with D36 the insurance is paid separately, so in_hand is 500000 and fees null. Ask her to update that line. Touches main.py and extract.py like Siddeshwar's #20: whichever merges second may need a small conflict fix.
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
