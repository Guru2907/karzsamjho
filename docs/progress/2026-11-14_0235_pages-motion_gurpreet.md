# H4, H5 · /how and /partners rebuilt with scroll components; borderless nav
- When: 14 Nov 2026, 2:35 AM IST · Who: agent for Gurpreet
- Did: after the lead's review. Nav: no pill and no outline; a borderless bar edge to edge, clear at the top and frosted glass (blur) once the page scrolls under it; links get a sliding underline. New components in web/src/site/fx.tsx, built with motion in the style of the kits the lead named (Aceternity and similar) but without glow or gradients: ScrollText (words light up as you scroll), StickySteps (text scrolls, a pinned panel swaps its picture), TypedLines (code wipes in line by line), HoverRows (big rows fill with the accent on hover), ScrollTimeline (a line that draws as you scroll). /how uses ScrollText, StickySteps with three pictures (ad -> form, the ledger, two readers compared), the typed maths.py block and a hover fallback list. /partners uses ScrollText, HoverRows for the three helpers and ScrollTimeline for the proposed pilot.
- Files: web/src/site/fx.tsx (new), web/src/site/SiteLayout.tsx, web/src/pages/How.tsx, web/src/pages/Partners.tsx
- Proof: `npm run build` OK, lint clean in these files. Headless-browser screenshots at 1440 x 900: /how at 6 scroll positions, /partners at 5, Home at 2 (nav clear at the top, frosted when scrolled); 0 px sideways overflow on all.
- Status in docs/TASKS.md: H4, H5 stay review
- Next: Gurpreet's look at the motion in a real browser.
- Broken / risks: the "second reader" picture on /how shows the case from our tests (a reader inventing an in-hand amount); phone-width layouts not checked.
