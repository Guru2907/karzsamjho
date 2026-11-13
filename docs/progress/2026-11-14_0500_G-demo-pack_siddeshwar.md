# G1 + G8 + G2 · demo pack: 10 images + 5 SMS + 5 harassment samples (D52)
- When: 14 Nov 2026, 4:45 AM IST (started) · Who: Siddeshwar (Claude Code)
- Did: (filled in as each phase finishes, see the Handover checklist below)
- Files: api/data/offers/demo/01.png..10.png, api/data/offers/demo_pack.json, api/data/offers/sms_demo.json, api/data/harassment/samples.json, api/data/README.md, scripts/make_demo_pack.py, scripts/run_demo_pack.py, api/tests/test_advance_fee.py (comment on line 3 only), docs/DEMO.md, docs/TASKS.md (G1, G2, G8), docs/DECISIONS.md (D52), this file. Removed: api/data/offers/ai_ad1.png, ai_ad2.png, ai_ad3.png, demo_expected.json, sms_offers.json, lender_demo.json
- Proof: (P4 results table below)
- Status in docs/TASKS.md: G1, G2, G8 = review (after P5)
- Next: see Handover
- Broken / risks: (filled in at P4 / P5)

## Rules for this task (from the brief, D52)
- After the 5:00 AM freeze: DATA + TESTING only. No change to api/core/, api/main.py, bot/ or web/.
- Synthetic data only; the only Aadhaar-like number is 1234 5678 9012.
- Every scam / costly / invented item uses an invented name checked NOT_FOUND with lender.match_lender.
- Real names only for KreditBee (listed app, FOUND) and Alok Auto Credit Pvt. Ltd. (RBI cancelled-registration list, warning), with ordinary terms and "Synthetic sample" on the item.
- Expected answers are written by hand BEFORE any run and never changed to match a run (K = 0).
- Images are drawn by a Pillow script, never an image AI.

## Handover (tick as each phase is committed and pushed; to take over: git pull on data/demo-pack, read this file, start at the first unticked phase)
- [x] P0 sync and start: branch data/demo-pack from main 05c9b21, pytest 600 passed, D52 added, this file, PR opened
- [x] P1 names + expected answers first: demo_pack.json (10), sms_demo.json (5), harassment/samples.json (5), name checks shown (below); hand arithmetic re-checked with the CLAUDE.md formulas: 0 errors
- [ ] P2 draw the 10 images: scripts/make_demo_pack.py -> api/data/offers/demo/01.png..10.png, checked by eye
- [ ] P3 remove the old data, update references (README, DEMO, TASKS, test comment), pytest passes
- [ ] P4 run everything through the real API: scripts/run_demo_pack.py, results table + K below
- [ ] P5 finish: PR description, G1/G2/G8 = review, tell Gurpreet "demo pack ready"

## P1: name checks (rule 2), run with api.core.lender.match_lender on main 05c9b21, before any image or run
"Patang Finance" was rejected: NOT_FOUND as an app, but it fuzzy-matched a REAL registered NBFC ("Patran Finance Private Limited"), so item 06 uses "Kulhad Capital Ltd." instead.
```
NOT_FOUND score=71.0  nbfc=no  warning=no   Gullak Go Finance Pvt. Ltd.  [01]
NOT_FOUND score=50.0  nbfc=no  warning=no   Gullak Go  [01]
NOT_FOUND score=50.0  nbfc=no  warning=no   GULKGO  [01 sender]
NOT_FOUND score=52.2  nbfc=no  warning=no   Jaldi Gullak  [02]
NOT_FOUND score=52.6  nbfc=no  warning=no   Sikka Swift  [03, sms1, harassment case]
NOT_FOUND score=52.6  nbfc=no  warning=no   Sikka Swift Instant Loan  [03]
NOT_FOUND score=0.0   nbfc=no  warning=no   गल्ला गो  [04]
NOT_FOUND score=53.3  nbfc=no  warning=no   Galla Go  [04 / 07]
NOT_FOUND score=53.3  nbfc=no  warning=no   Galla Go Loans  [07]
NOT_FOUND score=0.0   nbfc=no  warning=no   টুকরি টাকা  [05]
NOT_FOUND score=66.7  nbfc=no  warning=no   Tokri Taka  [05]
NOT_FOUND score=72.0  nbfc=no  warning=no   Kulhad Capital Ltd.  [06]
NOT_FOUND score=72.0  nbfc=no  warning=no   Kulhad Capital  [06]
NOT_FOUND score=0.0   nbfc=no  warning=no   घड्याळ क्रेडिट  [sms4]
NOT_FOUND score=66.7  nbfc=no  warning=no   Ghadyal Credit  [sms4]
NOT_FOUND score=63.2  nbfc=no  warning=no   Chillar Cash  [sms5]
FOUND     score=100.0 nbfc=yes warning=no   KreditBee  [08, sms2: real, expect FOUND]
SIMILAR   score=88.9  nbfc=no  warning=no   KreditBea  [09: lookalike, expect SIMILAR]
WARNING   score=72.7  nbfc=no  warning=yes  Alok Auto Credit Pvt. Ltd.  [10, sms3: real, expect WARNING]
```

## P1: design notes (decided before any run)
- Item 06: the brief said "Rs 5 lakh, 24 months, EMI Rs 27,000 -> COSTLY", but by our formula 27,000 x 24 = 6,48,000 is 15% a year = USUAL. EMI set to Rs 36,000 (37% a year -> COSTLY) so the item proves COSTLY as intended.
- Items 06 and 10 print the EMI count ("Number of EMIs: 24", "x 6 months"): the AI copies numbers and never calculates, so an implied count would make the item test our prompt instead of the backend.
- Item 01 prints the GST total ("total Rs 590") like a real KFS; the correct in-hand is 9410. If the reader uses Rs 500, in-hand 9500 is a wrong verified number: that would be a K finding, not a reason to change the answer.
- lender "WARNING" is not a lender.match value: the API returns match NOT_FOUND + lender.warning, so each item stores lender_flag (the brief's label) and lender_match / lender_warning (the API values).
- Not reachable in this pack: next steps FIND_CHEAPER, ASK_BANK_MITRA and SEND_CLEARER need a lender that is FOUND or not checked with a costly / unclear verdict; every costly item must carry an invented name (NOT_FOUND wins), and real names may only carry ordinary terms. Covered: all 4 verdicts, all 4 lender flags, next steps DO_NOT_PAY_FIRST, ON_WARNING_LIST, NOT_IN_RBI_LIST, CHECK_APP_NAME, KEEP_PAPERS.
