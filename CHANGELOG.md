# Changelog

Work after the hackathon goes under [Unreleased]. The hackathon build is the tag `colossus-submission`.

## [Unreleased]

### Docs
- Docs brought up to date after D60: ARCHITECTURE (hosting, the three doors, case codes, photos, PDF parts, closing, all tables, privacy), README (who uses what, 667 tests), CLAUDE.md (post-hackathon rules, lender match as coded: whole name, 92 / 80), AGENTS, RUNBOOK (bot on Render), TESTING (Postgres run), START_HERE, PROGRESS status, TASKS (post-hackathon section). PLAN and PREP are marked as history.

### Added (D60)
- Log a threat: a type of threat (death or physical harm, verbal abuse, legal or police, shaming, visit, other) and up to 3 photos. A type can add a rule (e.g. legal adds H5). Photos are cleaned of hidden location data and protected by the record's hash chain.
- Close a case: pick a reason, type CASE CLOSED to confirm. A closed case keeps its record, PDF and verify, takes no new threats, and shows under "Closed" on the Cases page. A threat forwarded to the bot after closing opens a new case.

### Changed (D60)
- The evidence PDF is in three parts: evidence from page 1, the complaint always from a new page, the photos from a new page. It shows the case status (open or closed).

### Fixed
- The complaint letter no longer doubles a full stop after a lender name ending in "." ("Ltd..").

### Changed (bot and app split, D59)
- Every harassment case gets an 8-digit code that never changes. In Telegram, /helper gives it; in the app, Cases -> type the code opens the case. The app no longer lists everyone's cases (only "Cases on this phone"), case ids are random, and the "list every case" API route is gone.
- The bot no longer sends the evidence PDF and /pdf is removed: the helper gets the PDF in the app. After a saved threat the bot says which rules broke and points to /helper.
- The bot asks once for the borrower's number (Telegram's share button) and keeps only the last 4 digits (XXXXXX 1234); the case and the PDF show it with the borrower's Telegram name and where the case came from. A helper can add a phone the same way when starting a case in the app.
- The bot remembers the chosen voice language and the chat's case in the database, so a restart forgets nothing.
- "Share with helper" is removed from the check result.

### Changed (database, D58)
- Hosted data now lives in Postgres on Neon instead of a SQLite file on Render's disk, so checks and harassment cases survive Render restarts and redeploys. Local work and tests still use SQLite.
- After a restart, a repeated photo is still answered from the database with no AI call, and a missing Hindi MP3 is made again on first play.

### Changed
- Website: no button opens the helper app on a laptop any more; "Get the app" buttons open a picture QR (the code itself forms a vegetable vendor's face) to scan with the phone. Phones get one "Open the app" button instead of the QR (D57).
- `/join` follows the light/dark theme like the other pages (its opening was always black).
- Helper app: new Home at `/app` (what it does, Check, Cases, the Telegram bot, how a check works); the install button moved there from `/check`; the installed app starts on Home.
- Light and dark: the saved theme is applied before the first paint (no light flash), and the phone status bar follows the theme.

### Fixed
- `/how` was wider than a phone screen (sideways scrolling); now fits at 360 px.
- `/how` limit "voice notes are understood in Hindi only" removed: Bengali and Marathi voice notes work.

## [colossus-submission] - 2026-11-14
COLOSSUS 3.0 submission (13-14 Nov 2026, FinTech track, Team Y2K Devs), built in about 21 hours. Commit `c5b4b0a`, the state of the code at judging (14 Nov 2026, 9:00 AM IST). Release: https://github.com/Guru2907/karzsamjho/releases/tag/colossus-submission

### Built
- Telegram bot: photo, pasted SMS or Hindi voice note -> rupee card (in hand, repay, days, extra) + Hindi voice; "pay first" scam warning.
- AI copies the printed numbers, Python does all the maths; a second model re-reads when numbers disagree; unclear numbers show "couldn't verify"; impossible readings (repay more than 10 times the loan) too.
- Lender check against RBI's published lists (digital lending apps, registered NBFCs, cancelled registrations) with the list date, and one next step per check.
- Harassment log: forwarded threats -> RBI recovery-agent rules H1-H5 -> hash-chained record -> English evidence PDF with masking and a tamper check.
- Backups: a second AI model when the first fails; the card still arrives without voice.
- Helper web app (check, cases, log threats and calls, PDF, verify; installable) and a public website.
- Hosted: web on Vercel, API on Render. 625 automated tests.

### Measured at submission
- Demo pack of 15 synthetic offers: 15 of 15 as expected, no wrong number shown as verified, median 2.3 s per check. Harassment samples: 5 of 5.

### Partial or missing
- Bengali and Marathi voices and listening: drafts, not approved by a native speaker.
- Rule H6 (5 or more calls a day) is in code, but calls cannot be logged from Telegram.
- Not built: WhatsApp, a consent step for keeping evidence, real-user testing. All test data is synthetic.
