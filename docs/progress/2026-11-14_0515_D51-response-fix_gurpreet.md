# Fix · D51 warning and NBFC were dropped from the API response
- When: 14 Nov 2026, 5:15 AM IST · Who: agent for Gurpreet (bug fix after the freeze)
- Did: found while reviewing Tejaswini's PR #57 with the real API: api/core/schemas.py's Lender response model did not list the D51 fields, so FastAPI dropped `nbfc` and `warning` from every response. The voice and next step were right (built before the response), but the Telegram card's ⚠️ line and the web card's warning never appeared. My Phase B real run called the pipeline function directly and missed it. Added the two optional models to Lender, plus two tests through HTTP.
- Files: api/core/schemas.py, api/tests/test_lender.py
- Proof: pytest 602 passed. Real API + PR #57's /check page: "Alok Auto Credit Pvt. Ltd." SMS now shows "RBI cancelled this company's NBFC registration · list as on 2026-09-30" on the card.
- Status in docs/TASKS.md: C3 stays review
- Next: merge before the demo; restart the API and the bot.
- Broken / risks: none known.
