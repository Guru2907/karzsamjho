# H8 · /join fixes after the lead's review
- When: 14 Nov 2026, 2:55 AM IST · Who: agent for Gurpreet
- Did: three fixes. (1) The opening was "the opposite of the theme", so in the dark theme it turned cream; it is now dark in BOTH themes, using two new colours that never flip (`--ink`, `--paper` in web/src/index.css; classes bg-ink, text-paper). (2) Over that block the nav keeps light text and frosts dark, instead of frosting in the page's light colour; after the block it behaves as on other pages. (3) The role picker starts on the first option (foundation), not the second. Also removed the long note under the buttons; the "public post" detail is now the button's hover tooltip.
- Files: web/src/pages/Join.tsx, web/src/site/SiteLayout.tsx, web/src/index.css
- Proof: `npm run build` OK, lint clean. Screenshots at 1440 x 900: dark theme at 4 scroll positions (top, mid-opening, next section, the letter) and light theme mid-opening; nav readable in all, no white flash.
- Status in docs/TASKS.md: H8 stays review
- Next: none.
- Broken / risks: none new. Tejaswini: `--ink` / `--paper` are for always-dark blocks only; everything else keeps using the normal tokens.
