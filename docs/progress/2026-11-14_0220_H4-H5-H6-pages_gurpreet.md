# H4, H5, H6 · /partners, /how and the custom 404
- When: 14 Nov 2026, 2:20 AM IST · Who: agent for Gurpreet
- Did: three more pages of the public website in the Home page's style, with shared building blocks (web/src/site/Page.tsx). /how: "The AI reads. Python calculates.": three jobs kept apart, the five lines of maths.py with the demo numbers, the fallback table, measured numbers, six limits. /partners: "Built for the helper beside Raju.": who it is for, what a helper gets, the commission idea clearly labelled as a proposed pilot that is not built, links to the app and the public repo (no forms, no login, no invented contact details). 404: a giant animated 404 that names the address it could not verify. The floating nav now links to both pages; every page starts at its top.
- Files: web/src/pages/How.tsx, Partners.tsx, NotFound.tsx, web/src/site/Page.tsx, web/src/site/shell.ts, web/src/site/SiteLayout.tsx, web/src/App.tsx, docs/TASKS.md, docs/DEMO.md
- Proof: `npm run build` OK. Headless-browser screenshots at 1440 x 900 of each page at 4 scroll positions (light), and the 404 in dark; 0 px sideways overflow on all three. One bug found that way and fixed (the outlined 0 of the 404 was clipped).
- Status in docs/TASKS.md: H4, H5, H6 = review
- Next: Gurpreet reviews the copy (every claim is from the repo: measured times from docs/TESTING.md, formulas from maths.py).
- Broken / risks: numbers on /how are written into the page (450+ tests, 3.9 s, 7.5 s); update them if the final 30-offer run (G6) gives different ones. Phone-width layouts not checked.
