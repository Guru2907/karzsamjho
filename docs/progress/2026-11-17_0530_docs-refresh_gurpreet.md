# P5 · Docs refresh after D60
- When: 17 Nov 2026, 5:30 AM IST (after the hackathon) · Who: agent for Gurpreet
- Did: brought every shared doc in line with the code after D57-D60. ARCHITECTURE rewritten (hosting, three doors, check and case flows, photos, PDF parts, verify, closing, all five tables, privacy). README, CLAUDE.md (post-hackathon process; lender rule as coded: whole-name ratio, >= 92 FOUND, 80-91 SIMILAR; bot/app split), AGENTS, RUNBOOK (bot on Render, Render env, dev-server workaround, new troubleshooting rows), TESTING (667, Postgres run), START_HERE (current-state box), PROGRESS status block (asked by Gurpreet), TASKS (post-hackathon section P1-P7). PLAN and PREP marked as history. No code changed.
- Files: README.md, CLAUDE.md, AGENTS.md, CHANGELOG.md, docs/{ARCHITECTURE,RUNBOOK,TESTING,START_HERE,PROGRESS,TASKS,PLAN,PREP}.md
- Proof: pytest -q 667 passed (unchanged); every number in the docs checked against the code (config.py thresholds, test count, routes in main.py).
- Status in docs/TASKS.md: P5 review
- Next: P6 (local dev server), P7 (code guessing limit), and the "keep local, not on GitHub" clean-up if agreed.
- Broken / risks: none (docs only).
