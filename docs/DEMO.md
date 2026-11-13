# DEMO.md: the 5-minute pitch and live demo

Anyone who changes a flow the demo shows updates this file in the same commit.

Stage roles (to be assigned): presenter · phone · laptop · technical answers.

## Timeline
| Time | What happens | Words (gist) |
|---|---|---|
| 0:00-0:20 | Question to the room | "Who here has read the full terms of a loan app before tapping Accept?" |
| 0:20-0:45 | Raju + evidence | Raju needs Rs 5,000 tonight. Only 1 in 3 digital-loan users knew what a key fact statement is (FACE, 2024). Add one real quote if we talked to a vendor |
| 0:45-1:00 | Cost | "Rs 3,800 in hand, Rs 5,000 back in a week. Rs 1,200 extra. He finds out after he signs." |
| 1:00-1:10 | Solution | "Send a photo. Hear the cost in rupees, in your language." |
| 1:10-2:00 | LIVE 1: Snap & hear | Phone photographs printed ad 1 in Telegram; speaker plays the Hindi; hold up the card and the seconds stamp |
| 2:00-2:20 | LIVE 2: Next step | "Not found in RBI's directory" + one next step; laptop shows helper view with the maths |
| 2:20-3:05 | LIVE 3: Harassment log | Forward a threat timed 9:40 PM; case page shows H1 + H2; PDF opens; draft letter; "Day 1 of 30" |
| 3:05-3:30 | Before / after | Before: learns the cost after a week, screenshots scattered. After: hears it in T s; evidence in under a minute |
| 3:30-4:05 | Proof and limits | Measured 30-offer result incl. misses. "Synthetic ads. We can't stop someone borrowing. We tell him the cost first." |
| 4:05-4:25 | How it's built | One picture: "The AI reads, plain code does the maths, a second model re-reads when numbers disagree." No jargon |
| 4:25-4:40 | Team | "Y2K Devs: four students from Bengaluru, two colleges. We topped Round 1 out of 522, and today we built what we promised." |
| 4:40-5:00 | Plan kept + close | Deck roadmap beside real commit times. "Loan lene se pehle, suno." |

## Luck-proofing
1. Use the 3 printed ads that are already run and cached. A fresh photo only if time allows.
2. Telegram stalls 5 s -> laptop runs the same ad on /check.
3. Voice fails -> "the card works without audio", move on.
4. Network gone -> backup video from the matching point; keep talking.
5. Nobody types live. Speaker paired and charged.
6. Landing page is not in the 5 minutes; open only if asked about NGOs or design.
7. Over 5:00 in rehearsal -> cut words, don't speed up.

## Demo assets checklist
- [ ] 3 printed ads (2 copies each), pre-run and cached on the server
- [ ] Threat message ready to forward on the phone
- [ ] Browser tabs open in order: /check (helper view), /cases/:id
- [ ] Backup video: 60 s clip (7:30 PM) and full run (3:00 AM)
- [ ] Final numbers filled from docs/TESTING.md
- [ ] Speaker paired, phone at 100%, hotspot ready
- [ ] Seconds stamp for LIVE 1: the Telegram card does not show seconds (only the API result has `seconds`). Show it on /check, or ask for it on the card before the 3:30 AM freeze
- [ ] LIVE 2 needs the lender check (C1) and next step (C2); tonight the card has no RBI line and one fixed next step (D26)

## Never say
"100%", "illegal", "guaranteed", "the Ombudsman accepts this", "real users tested it" (unless they did), anything we did not build.

## Hard questions (short honest answers)
1. AI misreads? Code cross-checks; second model on mismatch; disagreement = "couldn't verify"; on 30 offers K got through.
2. Your own test ads? Yes, synthetic. Field testing is next.
3. "Not found" = illegal? No; directory is self-reported, names vary.
4. 1,647% fair? Simple yearly rate; Raju hears Rs 1,200 extra in 7 days.
5. Who decides "very costly"? We do; three thresholds in config; not an RBI limit.
6. Why Telegram? WhatsApp business API needs approval and money; browser version works from a QR.
7. Vs LoanLens / V.A.R.U.N.? Written analysis / general companion; we speak this exact offer's rupees and turn harassment into a rule-cited record.
8. Ombudsman accepts the PDF? Don't know; follows RBI's published route; dates, times and rules in one place.
9. Privacy? Synthetic data; free tiers may train on inputs, so production needs paid or self-hosted; photos deleted; IDs masked.
10. Evidence faked? Can't prove a message is genuine; the hash chain proves no edits after logging.
11. Built before today? Show docs/PREP.md; repo starts 11:30 AM.
12. Why would a bank mitra bother? Our assumption, not a finding; a pilot tests it.
