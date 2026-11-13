# H1, H3 · Home polish after the lead's review
- When: 14 Nov 2026, 2:10 AM IST · Who: agent for Gurpreet
- Did: the top bar looked out of place (a narrow centred bar over an edge-to-edge hero), so it is now a floating pill that slides away on scroll down and returns on scroll up (the Aceternity "floating navbar" idea, built with motion directly). The pinned phone story is shorter: 260% of the screen instead of 440%. Hero fills the screen under the pill, the two headline lines sit together, and a hairline strip of three facts sits at the bottom. Footer: the wordmark outlined at full width.
- Files: web/src/site/SiteLayout.tsx, web/src/site/Story.tsx, web/src/site/shell.ts, web/src/pages/Landing.tsx
- Proof: `npm run build` OK; headless-browser screenshots at 1440 x 900 of the hero, the last story stage and the footer checked; 0 px sideways overflow.
- Status in docs/TASKS.md: H1, H3 stay review
- Next: /how, /partners and the 404 in a second PR.
- Broken / risks: none new.
