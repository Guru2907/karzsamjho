# G1 · demo pack: image 04 tear-off tabs, image 10 in the phone frame (review fix on PR #56)
- When: 14 Nov 2026, 5:50 AM IST · Who: agent for Gurpreet (on Siddeshwar's branch, after his P5)
- Did: 04.png's five tear-off slips were empty boxes that look like missing characters when printed; each now carries the lender's name ("गल्ला गो लोन", the same line as the headline, so nothing new for the reader). 10.png moves from the plain card into the same neutral grey phone-SMS frame as 08.png, sender "Sample SMS" (not the company name: the RBI cancelled-registration warning needs the exact name, read from the message, which now starts "Alok Auto Credit Pvt. Ltd.: ..."). Only item 10's text_on_image and looks_like changed in demo_pack.json; no expected answer changed.
- Files: scripts/make_demo_pack.py, api/data/offers/demo_pack.json (item 10 text only), api/data/offers/demo/04.png, demo/10.png
- Proof: re-rendering changes only 04 and 10 (the other 8 are byte-identical); a second run changes nothing. Real API (qwen): 10 -> 14700 / 16800 / 180 days / 2100, USUAL, warning "Alok Auto Credit Pvt. Ltd.", next step ON_WARNING_LIST (2.4 s); 04 -> 50000 / 60000 / 90 days / 10000, COSTLY, pay_first -> DO_NOT_PAY_FIRST (9.7 s). Both equal the hand-written expected answers.
- Status in docs/TASKS.md: G1 stays review
- Next: print the pack (G3).
- Broken / risks: none known.
