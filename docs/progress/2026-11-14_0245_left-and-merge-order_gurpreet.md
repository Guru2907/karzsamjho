# Check of all open PRs + what is left + merge order
- When: 14 Nov 2026, 2:45 AM IST · Who: agent for Gurpreet
- Did: merged all 11 open PRs together in a throwaway copy of main and ran the tests and the web build; checked Siddeshwar's D45 list against his PRs and read the code of C2, B12, F6; found what is still missing (RBI list empty, web app placeholders, no harassment samples); wrote the "Left at 2:45 AM" section at the end of docs/TASKS.md with the merge order.
- Files: docs/TASKS.md (new section at the end only), this file
- Proof: combined merge: 571 passed; web build OK. Order tested twice: website first (one clash on #48) and backend first (one clash on #45, fixed on our own branch, so the recommended order).
- Status in docs/TASKS.md: no task status changed (Siddeshwar's tasks go to done after merge, by someone other than him)
- Next: after "backend merged", fix the DECISIONS.md clash on docs/website-plan and pass it up the website chain.
- Broken / risks: G4 RBI CSV and Tejaswini's E tasks are the two biggest risks to the demo.
