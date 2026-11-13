# Handover to Siddeshwar (D45) + new feature numbers
- When: 14 Nov 2026, 1:20 AM IST · Who: agent for Gurpreet
- Did: main = 8a62070 (40 PRs, 457 tests, 0 open PRs). Siddeshwar now owns all backend and bot code and takes C2, F6, D9, D10, B12, D8, C3, B13, D11; Gurpreet moves to the landing page (H1-H3); Tejaswini keeps the web app; Anam the data. Numbered the new features: B12 (photo pay-first confirmed by the second reader), B13 (Bengali / Marathi regex backup), F6 (complaint letter addressee follows the route). Full prompt for Siddeshwar in docs/PLAN.md "Handover at 1:20 AM". NGO onboarding noted as a later discussion, not a task.
- Files: docs/PLAN.md, docs/TASKS.md, docs/DECISIONS.md (D45), docs/PROGRESS.md (status), this file
- Proof: docs only; `pytest -q` 457 passed on main.
- Status in docs/TASKS.md: owners changed; B12, B13, F6 added
- Next: Siddeshwar C2 then F6; Gurpreet H1-H3; Anam G4.
- Broken / risks: RBI CSV still empty; no web PRs yet; bn/mr sentences await the native-speaker OK.
