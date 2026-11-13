# api/data

Synthetic and public data only. No real borrower data.

## Ledger Files
Rebuild needs: `pip install openpyxl`
Rebuild command: `python scripts/build_ledger.py`

- `rbi_dla.csv`: RBI's directory of digital lending apps (task G4).
  - Columns: `dla_name,regulated_entity,website,list_date`
  - Rebuilt from `api/data/raw/rbi_dla.xlsx`
- `rbi_nbfc.csv`: RBI's list of registered NBFCs (task C3 data).
  - Columns: `nbfc_name,former_name,cin,regional_office,classification,list_date,source_url`
  - Rebuilt from `api/data/raw/rbi_nbfc.xlsx`
- `watch_list.csv`: Official warnings and cancelled NBFC registrations (task C3 data).
  - Columns: `name,website,list_name,source_type,source_url,source_date,note`
  - Rebuilt from `api/data/raw/rbi_cancelled_nbfc.xlsx`

## Demo pack (G1, G8, G2; decision D52)
One pack that shows every backend path through the Telegram bot. Everything is synthetic. Every name on a
scam or costly item is invented and was checked NOT_FOUND with `api.core.lender.match_lender` before use.
The only real names are KreditBee (a listed app) and Alok Auto Credit Pvt. Ltd. (on RBI's cancelled-registration
list), with ordinary terms and "Synthetic sample" on the item. Expected answers were worked out by hand with the
formulas in CLAUDE.md BEFORE any run and are never changed to match a run (K = 0).

- `offers/demo/01.png` ... `10.png`: 10 offer images to print (A5) and photograph, or send straight to the bot.
- `offers/demo_pack.json`: for each image, every line of text on it (`text_on_image`), the hand-worked `expected`
  answer, the working (`hand_working`) and what it `proves`:

  | Image | Looks like | Shows |
  |---|---|---|
  | 01 | SMS screenshot, invented NBFC | EMI x count = repay, in-hand derived, USUAL, NOT_FOUND |
  | 02 | glossy app ad "Jaldi Gullak" | the Raju story: Rs 3,800 in hand, Rs 1,200 extra in 7 days, VERY_COSTLY |
  | 03 | WhatsApp forward | pay Rs 1,499 first -> "Paise mat bhejo" warning (both AI readers agree), DO_NOT_PAY_FIRST |
  | 04 | Hindi pamphlet | Devanagari, "50 हज़ार" -> 50,000, pay Rs 999 first, COSTLY |
  | 05 | Bengali SMS, Bengali digits | Bengali read from a photo; use with /bhasha = bn |
  | 06 | bank-style email | "₹5 lakh" -> 5,00,000, EMI x 24, COSTLY |
  | 07 | flyer whose numbers do not add up | cross-check + second reading -> CANNOT_SAY |
  | 08 | SMS "KreditBee" (real, ordinary terms) | FOUND in RBI's list + registered NBFC |
  | 09 | SMS "KreditBea" + link | SIMILAR: check the exact name |
  | 10 | notice "Alok Auto Credit Pvt. Ltd." (real, ordinary terms) | RBI cancelled registration -> warning |
- `offers/sms_demo.json`: 5 SMS to paste live: 1 Hinglish pay-first scam (also read aloud as a voice note),
  2 KreditBee (FOUND), 3 Alok Auto Credit (warning), 4 Marathi, 5 "50 hazaar" / "60k" amounts. Same `expected` fields.
- `harassment/samples.json`: 5 recovery messages with `expected_rules` (H2+H4, H3, H5 with the synthetic Aadhaar
  1234 5678 9012 that the PDF must mask, H1+H2 at 11:30 PM, and a polite reminder with no rule).

Field meanings are in `demo_pack.json` -> `expected_fields`. Note: "WARNING" is not a `lender.match` value; the API
returns `match` NOT_FOUND plus a filled `lender.warning`, so each item stores `lender_flag` and `lender_match` /
`lender_warning`.

### Redraw the images
```
pip install pillow uharfbuzz freetype-py      # locally only, not in api/requirements.txt
python scripts/make_demo_pack.py              # -> api/data/offers/demo/01.png ... 10.png
```
Edit `text_on_image` in `demo_pack.json`, never the PNGs. The script draws only those lines (it stops if one is
missing), shapes Hindi / Bengali with HarfBuzz (this Pillow has no libraqm), stops on a missing glyph, and gives the
same files on every run. Fonts: Windows Segoe UI and Nirmala UI.

### Run the pack through the real API
```
scripts\run_api.bat                           # in another window
python scripts/run_demo_pack.py               # expected vs got for every image, SMS and harassment sample, and K
```

## Other files
- `harassment/`: `samples.json` (above).
- `raw/`: Official RBI XLSX raw files used by `scripts/build_ledger.py`.
- `SOURCES.md`: Detailed metadata, source URLs, download dates, row counts, and cleaning rules.
