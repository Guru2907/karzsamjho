# PWA · open a harassment case from the helper app (D56, freeze exception by the lead)
- When: 14 Nov 2026, 7:50 AM IST · Who: agent for Gurpreet
- Did: web/src/components/cases/NewCaseDialog.tsx (borrower + lender -> api.createCase -> case page). Used on /cases ("New case") and on a /check result ("Being threatened? Start a case", lender pre-filled, check_id linked). Empty-state text on /cases updated. No API change (POST /api/cases already existed).
- Files: web/src/components/cases/NewCaseDialog.tsx (new), web/src/pages/Cases.tsx, web/src/pages/Check.tsx, docs/DECISIONS.md (D56), docs/DEMO.md
- Proof: build + lint clean. Browser at 400 px, local API: /cases -> New case "Demo borrower / Sikka Swift" -> case_0002, Sachet + 1930; /check SMS "Gullak Go Loan ..." -> result -> Start a case (lender pre-filled) -> case_0003 linked to chk_0021, Sachet + 1930, Log a threat ready.
- Status in docs/TASKS.md: E4, E5 stay review
- Next: merge BEFORE setting up demo cases (a merge redeploys Render and empties it).
- Broken / risks: none known.
