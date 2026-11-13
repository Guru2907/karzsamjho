# H1 (W1) · website foundation: palette, two layouts, hero preview
- When: 14 Nov 2026, 2:00 AM IST · Who: agent for Gurpreet
- Did: palette tokens in web/src/index.css (cream, near-black, burnt orange; light + dark; one radius), so the PWA picks them up too. App.tsx now has two layouts: the public website (web/src/site/SiteLayout.tsx, own nav + footer) for "/" and the PWA layout with the app top bar for /check and /cases; the top bar no longer links to "/". Hero on "/": word-by-word headline, phone frame with the demo card counting up to 3,800 / 5,000 / 1,200, play button for the real sample Hindi MP3, three measured facts. Added `motion` and `qrcode.react` (website only). Motion helpers respect prefers-reduced-motion.
- Files: web/src/index.css, web/src/App.tsx, web/src/components/TopBar.tsx, web/src/pages/Landing.tsx, web/src/site/ (SiteLayout.tsx, PhoneCard.tsx, motion.tsx, shell.ts), web/public/sample-hi.mp3, web/package.json + lockfile, docs/TASKS.md
- Proof: `npm run build` OK, `npm run lint` no warnings in the new files. Headless-browser screenshots checked: laptop width light and dark, a true 400 px width (no sideways overflow), and /check still with its own bar in the new palette.
- Status in docs/TASKS.md: H1 = doing
- Next: Gurpreet looks at http://localhost:5173/ and approves the look; then W2 (rest of Home).
- Broken / risks: Tejaswini must pull before pushing (App.tsx, index.css, TopBar.tsx, package.json changed). The JS bundle grew from 341 kB to 509 kB with motion.
