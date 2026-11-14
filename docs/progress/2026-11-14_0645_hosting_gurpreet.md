# Hosting · API on Render, web on Vercel (web/vercel.json)
- When: 14 Nov 2026, 6:45 AM IST · Who: agent for Gurpreet (Gurpreet set up Render)
- Did: Gurpreet created the Render web service; added web/vercel.json (forward /api/* to https://karzsamjho-api.onrender.com, every other path to index.html) and a "Hosting" section in docs/RUNBOOK.md (settings, keys only in the dashboard, free-tier sleep and disk reset, UptimeRobot, how to install on phones / laptop).
- Files: web/vercel.json, docs/RUNBOOK.md
- Proof: hosted /api/health: api up, groq + gemini + edge-tts up, database up. Real SMS check on the hosted API (Alok Auto Credit): 14700 / 16800 / 180 days / 2100, USUAL, RBI cancelled-registration warning, next step ON_WARNING_LIST, 3.0 s; its MP3 downloads (200, audio/mpeg, 153 KB).
- Status in docs/TASKS.md: no task change (hosting is ops)
- Next: Gurpreet imports the repo in Vercel (Root Directory web); bot API_URL -> Render; test install on phones.
- Broken / risks: free Render sleeps after 15 min and resets its disk; keep it awake with UptimeRobot and do not redeploy after demo cases are set up.
