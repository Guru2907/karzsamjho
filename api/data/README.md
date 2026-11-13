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

## Test Data
- `offers/`: Synthetic loan offers and expected answers (task G1).
  - `demo_expected.json`: 3 AI-made ad evaluations.
  - `sms_offers.json`: 3 cleaned synthetic scam/loan SMS offers.
  - `lender_demo.json`: 4 synthetic offers testing FOUND, SIMILAR, NOT_FOUND, and WARNING lender states.
- `harassment/`: 10 harassment samples and their expected rules (task G2).
- `raw/`: Official RBI XLSX raw files used by `scripts/build_ledger.py`.
- `SOURCES.md`: Detailed metadata, source URLs, download dates, row counts, and cleaning rules.
