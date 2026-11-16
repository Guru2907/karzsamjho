# PR A (D58) · Database on Neon Postgres
- When: 17 Nov 2026, 2:30 AM IST (after the hackathon) · Who: agent for Gurpreet
- Did: api/core/db.py runs on Postgres (Neon) when DATABASE_URL is set, on the SQLite file otherwise; same SQL for both, a small connection pool for Neon. checks gets a lang column. The cache falls back to the database by photo key; /api/audio makes a missing MP3 again from the stored sentence in the check's language.
- Files: api/core/db.py, api/core/config.py, api/core/cache.py, api/main.py, api/requirements.txt, api/tests/conftest.py, api/tests/test_cache.py, api/tests/test_cases.py, .env.example, CLAUDE.md, README.md, docs/ARCHITECTURE.md, docs/RUNBOOK.md, docs/DECISIONS.md, CHANGELOG.md.
- Proof: pytest 625 passed on SQLite; the same 625 passed on Neon (KS_TEST_DATABASE_URL, throw-away schema, dropped afterwards, 0 left). Real server on Neon: SMS + photo check, case + event (H1, H3, H5); restart with cache files and MP3s wiped -> check still there, MP3 rebuilt (200, audio/mpeg), same photo answered from the database with no AI call (cached, same id), case + verify ok + PDF. Test rows deleted (0, 0, 0).
- Status in docs/TASKS.md: no task row (post-hackathon; CHANGELOG [Unreleased]).
- Next: Gurpreet merges, then adds DATABASE_URL in Render's Environment (Render redeploys). Then PR B (case codes, bot memory in the database).
- Broken / risks: Neon free tier sleeps after ~5 min idle (first query ~1 s slower); UptimeRobot's /api/health ping keeps it awake. Old data on Render's disk is not copied (it is wiped on redeploy anyway).
