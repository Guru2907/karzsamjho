# Fix · E7 Easy mode switch did nothing; QR's ?mode=raju could not be turned off
- When: 14 Nov 2026, 6:15 AM IST · Who: agent for Gurpreet (bug fix after the freeze)
- Did: web/src/lib/raju.ts sent its change event from inside a React state update, so the top bar and /check updated each other while rendering (React: "Cannot update a component while rendering a different component") and the Easy mode switch did nothing; with ?mode=raju in the address it could not be turned off, and a reload or a trip to Cases forced it back on. Rewritten as one shared store with useSyncExternalStore (localStorage "ks-raju", memory fallback); ?mode=raju switches it on once and is removed from the address. Same hook signature, so TopBar and Check are unchanged.
- Files: web/src/lib/raju.ts
- Proof: npm run build OK, lint clean. Headless browser at 400 px, step by step: switch on -> one big camera button; off -> normal screen; /check?mode=raju -> on and the address cleaned; off -> stays off after reload and after /cases -> /check; no React warnings in the console (before: the switch stayed off and 2 "Cannot update a component" warnings).
- Status in docs/TASKS.md: E7 stays review
- Next: none.
- Broken / risks: none known.
