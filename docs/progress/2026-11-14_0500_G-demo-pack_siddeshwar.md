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
- [ ] P1 names + expected answers first: demo_pack.json (10), sms_demo.json (5), harassment/samples.json (5), name checks shown
- [ ] P2 draw the 10 images: scripts/make_demo_pack.py -> api/data/offers/demo/01.png..10.png, checked by eye
- [ ] P3 remove the old data, update references (README, DEMO, TASKS, test comment), pytest passes
- [ ] P4 run everything through the real API: scripts/run_demo_pack.py, results table + K below
- [ ] P5 finish: PR description, G1/G2/G8 = review, tell Gurpreet "demo pack ready"
