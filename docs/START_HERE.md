# START HERE

This zip is the full KarzSamjho starter repo. It includes an **empty `.env`**, which GitHub never carries for you.

> **Never put real keys in this zip, and never send a filled `.env` in any chat.** If that happens, delete the key in the provider's console and make a new one.

**Folders:** `api/` = backend · `web/` = frontend · `bot/` = Telegram bot · `scripts/` = setup and run scripts · `docs/` + the `.md` files at the top = shared memory for us and our AI agents (these ARE committed to GitHub, on purpose).

**You need:** Python 3.11+ (tick "Add to PATH" when installing), Node.js 20+ (LTS), Git.

---

## A. Lead (server laptop), once

**1. Unzip and open a terminal in the folder**
Unzip, open the `karzsamjho` folder, click the address bar, type `cmd`, press Enter.

**2. Install everything** (backend + frontend, takes a few minutes)
```
scripts\setup.bat
```
Wait for "Setup done".

**3. Fill in the keys**
```
notepad .env
```
Paste the **demo** bot token, Gemini key and Groq key after the `=` (no spaces, no quotes). Save. Check:
```
.venv\Scripts\python scripts\check_env.py
```
You want "All required keys are set." (It never prints the keys.)

**4. Push to GitHub**
```
git init -b main
git add .
git status
```
Make sure `.env` is **not** in the list. Then:
```
git commit -m "setup: starter repo"
git remote add origin https://github.com/<you>/karzsamjho.git
git push -u origin main
```
On GitHub: Settings → Collaborators → add the 3 teammates. Turn on branch protection for `main`.

**5. Run it** (see section C) and check the 2:00 PM gate (section D).

---

## B. Teammates, once

**1. Clone** (do NOT work inside the unzipped folder, it has no link to GitHub):
```
git clone https://github.com/<lead>/karzsamjho.git
cd karzsamjho
```
**2. Install:**
```
scripts\setup.bat
```
**3. Keys:** `notepad .env` and fill in **your own** Gemini key, **your own** Groq key and the **TEST** bot token. Only the server laptop uses the demo bot token. Check with `.venv\Scripts\python scripts\check_env.py`.

---

## C. Run (every time, three terminals in the `karzsamjho` folder)

| Terminal | Windows | Mac/Linux |
|---|---|---|
| 1. API | `scripts\run_api.bat` | `scripts/run_api.sh` |
| 2. Bot | `scripts\run_bot.bat` | `scripts/run_bot.sh` |
| 3. Web | `scripts\run_web.bat` | `scripts/run_web.sh` |

Start the API first. You only need the parts your task touches (web-only work = API + web). Stop anything with `Ctrl + C`. No reinstalling, except: after a `git pull` that added a package, run `scripts\setup.bat` again.

---

## D. Check it works

- http://localhost:8000/api/health shows `"api":"up"` and your keys as `true`
- Send a loan ad photo or paste a loan SMS to your bot in Telegram: the ₹ card comes back, then a Hindi MP3
- Send something that is not a loan: a polite Hindi "Yeh loan ka offer nahi lagta" and no card
- Tests: `.venv\Scripts\python -m pytest -q` (266 passed on main at 9:00 PM, 13 Nov)

Checks are **real** since 6:00 PM, 13 Nov (photo/text -> AI reads -> Python maths -> verdict -> Hindi voice). Still sample data: cases, events, evidence PDF, verify. The `/check` page still shows the old placeholder until the PWA work (E2, E3, E9) is merged. Results are kept in memory, so they disappear when the API restarts (database: task A3).

---

## E. Doing a task (everyone, every task)

1. **Get the latest:** `git checkout main` then `git pull`
2. **New branch:** `git checkout -b b3-maths` (task ID + short name)
3. **Tell your agent:**
   > Read CLAUDE.md, docs/PROGRESS.md and docs/DECISIONS.md, then do task B3.
4. Read its plan → approve → let it code → **read the diff** → **run it**.
5. Before committing, check the agent:
   - added an entry at the **top** of `docs/PROGRESS.md`
   - set the task's Status in `docs/TASKS.md` (review)
   - added to `docs/DECISIONS.md` if something was decided
6. Commit code **and** docs together, push, open a pull request:
   ```
   git add .
   git commit -m "maths: add rupee maths + tests"
   git push -u origin b3-maths
   ```
7. Tell Gurpreet; he checks and merges (D27). Nobody else merges and nobody pushes to `main`. Then `/clear` the agent before the next task.
   - Gurpreet merges with **"Create a merge commit"** (never squash) and ticks **"Merge without waiting for requirements to be met"** (D28).
   - If your task builds on a branch that is not merged yet, start your branch from that branch and say "merge after #N" in the PR.

**Merge conflict in PROGRESS.md?** Normal (two people added entries at the top). Keep both entries, delete the `<<<<<<<`, `=======`, `>>>>>>>` lines, commit.

**The "Current status" block** at the top of PROGRESS.md: updated by the lead, or by whoever passes a gate.

---

## F. If something breaks

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Install Python 3.11+, tick "Add to PATH", reopen the terminal |
| `'npm' is not recognized` | Install Node.js 20+ (LTS), reopen the terminal |
| Bot says "Conflict" | Another program uses the same bot token. Close it |
| Bot replies "Server abhi band hai" | Start `run_api.bat` first |
| /check says "Could not reach the API" | Start the API |
| Phone can't open the site | Use `http://<laptop IP>:5173` (`ipconfig` → IPv4), allow Python and Node in Windows Firewall, or put both on one hotspot |
| A key leaked | Delete it in the provider console, make a new one, update `.env` |

More fixes: `docs/RUNBOOK.md`.

## Gates (IST)
13 Nov **2:00 PM** photo in Telegram gets a reply · **7:30 PM** 3 printed ads → voice + card, twice · 14 Nov **12:30 AM** all 4 features pass · **3:30 AM** feature freeze · **9:00 AM** submission
