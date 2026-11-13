# docs sync + progress entries as separate files (D43)
- When: 14 Nov 2026, 12:55 AM IST · Who: agent for Gurpreet
- Did: all 37 PRs are on main (440 tests). Brought every doc in line with main: CLAUDE.md, AGENTS.md, README, START_HERE, ARCHITECTURE, TESTING, RUNBOOK, DEMO, PLAN, TASKS, PROGRESS status; fixed the stale header comment in api/main.py. Progress entries are now one file each in docs/progress/ (D43), so PROGRESS.md no longer conflicts on every merge; scripts/show_progress.py prints the newest.
- Files: CLAUDE.md, AGENTS.md, README.md, api/main.py (comment only), docs/*.md, docs/progress/, scripts/show_progress.py
- Proof: `pytest -q` 440 passed on main (f9b0c6b); docs and one comment only.
- Status in docs/TASKS.md: unchanged except notes on D5, F3, F4
- Next: real end-to-end check on main; F4 verify (the PDF promises it); Anam's RBI CSV (G4).
- Broken / risks: verify (F4) still always answers ok; RBI CSV empty, so the lender check says "not checked"; no web pages (E) yet; bn/mr sentences await the native-speaker OK.
