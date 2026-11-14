# PWA · "Install KarzSamjho" button on /check (D54, freeze exception by the lead)
- When: 14 Nov 2026, 7:00 AM IST · Who: agent for Gurpreet
- Did: web/src/components/InstallPrompt.tsx: listens for the browser's install offer from app start, shows "Install KarzSamjho on this phone" (one tap opens the phone's own install window), an iPhone hint "To install: tap Share, then Add to Home Screen", nothing when already installed or no offer. Placed at the top of the /check start screen.
- Files: web/src/components/InstallPrompt.tsx (new), web/src/pages/Check.tsx (2 lines), docs/DECISIONS.md (D54)
- Proof: build + lint clean. Headless browser at 400 px: install offer -> button shown; tap -> install window opened, button gone after accepting; iPhone (no offer) -> the Share hint; desktop without an offer -> nothing.
- Status in docs/TASKS.md: no task change (part of the PWA, E6 follow-up)
- Next: after merge Vercel redeploys; scan the helper QR on an Android phone and tap Install.
- Broken / risks: browsers decide when to make the offer (Chrome may wait until the site has been used briefly); the menu route (⋮ > Install app) still works.
