# docs/progress: one file per progress entry (D43)

Each task adds ONE new file here in the same pull request, instead of editing docs/PROGRESS.md.
Two pull requests then never change the same lines, so they never conflict.

- Name: `YYYY-MM-DD_HHMM_<task>_<person>.md` (IST, 24-hour), e.g. `2026-11-14_0105_F4_gurpreet.md`.
  The names sort by time, newest last.
- Never edit or delete someone else's file. A correction is a new file.
- Read the newest ones: `python scripts/show_progress.py` (or `python scripts/show_progress.py 15`).
- Only the "Current status" block at the top of docs/PROGRESS.md is still shared; Gurpreet updates it.
- Entries before 14 Nov 12:55 AM are in docs/PROGRESS.md under "Log (history)".

Template (copy into a new file):
```
# <task ID(s)> · <short title>
- When: <date, time IST> · Who: <person, or "agent for <person>">
- Did: <one or two lines>
- Files: <paths>
- Proof: <test command + result, or "tested in Telegram: ...">
- Status in docs/TASKS.md: <review | done>
- Next: <the next step for this area>
- Broken / risks: <anything another person must know, or "none">
```
