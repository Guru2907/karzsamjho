# P9 · Screenshots in the README
- When: 24 Nov 2026, 10:10 AM IST · Who: agent for Siddeshwar
- Did: GitHub had no pictures of the project (only app icons and the QR). Added eight screenshots and a "Screenshots" section in the README: the website, the helper app's home, three check results (Jaldi Gullak: ₹3,800 in hand, ₹5,000 back, ₹1,200 extra; KreditBee found in RBI's list; Alok Auto Credit's cancelled registration), a harassment case, its timeline with rules H1, H2, H4, H5 and a masked Aadhaar, and page 1 of the evidence PDF. No code changed.
- Files: docs/media/screenshots/*.png (8 files, 1.1 MB in all), README.md, CHANGELOG.md, docs/TASKS.md (P9)
- Proof: every picture was looked at before the commit; the numbers on the three cards are the demo pack's expected answers. `pytest -q` -> 667 passed (nothing in api/, bot/ or web/ changed).
- Status in docs/TASKS.md: review
- Next: a Telegram screenshot (the borrower's side) if someone takes one on a phone; it cannot be captured from a browser.
- Broken / risks: this branch is built on top of the video branch (PR #73), because both add a section at the same place in the README; merge #73 first. Pictures were taken on a local copy of the app with its own throwaway database, synthetic samples only. They show the app as it is on 24 Nov; a later design change needs new pictures.
