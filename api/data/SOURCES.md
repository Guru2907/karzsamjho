# Data Sources (Lender Ledger)

All raw files downloaded by hand from `rbi.org.in` (the site blocks programmatic scripts via F5 BIG-IP / SAP Web challenge). Rebuild is automated via `python scripts/build_ledger.py`.

---

## 1. `rbi_dla.csv` — RBI Directory of Digital Lending Apps (G4)
- **Source URL**: `https://data.rbi.org.in/BOE/OpenDocument/opendoc/custom.jsp?sIDType=CUID&iDocID=ARfEgy.WNSVIvFfvSIVmBCw` (RBI Citizen's Corner: "DLAs deployed by Regulated Entities")
- **How downloaded**: Downloaded by hand from rbi.org.in as `api/data/raw/rbi_dla.xlsx`
- **Download date**: 2026-11-14
- **As on date**: 2026-11-14 (download date, no date shown on the RBI page)
- **Row count**: 2,811 rows (1,222 distinct DLA names)
- **Columns**: `dla_name,regulated_entity,website,list_date`
- **Cleaning**: Carried down merged `Entity Name` cells, extracted Play Store URLs (`?id=`) or direct website links, excluded Apple App Store links and email addresses.

---

## 2. `rbi_nbfc.csv` — RBI Registered NBFCs List (C3 Data)
- **Source URL**: `https://rbidocs.rbi.org.in/rdocs/content/DOCs/List_of_NBFCs_and_ARCs_registered_with_the_RBI.XLSX` (from `https://www.rbi.org.in/scripts/BS_NBFCList.aspx`)
- **How downloaded**: Downloaded by hand from rbi.org.in as `api/data/raw/rbi_nbfc.xlsx`
- **Download date**: 2026-11-14
- **As on date**: 2026-09-30
- **Row count**: 8,502 rows (573 with a former_name)
- **Columns**: `nbfc_name,former_name,cin,regional_office,classification,list_date,source_url`
- **Cleaning**: Kept rows with valid integer serial number (drops footnote), split former company names (`(Formerly: ...)`).

---

## 3. `watch_list.csv` — NBFC Cancelled CoR Watch List (C3 Data)
- **Source URL**: `https://rbidocs.rbi.org.in/rdocs/content/DOCs/List_of_NBFCs_and_ARCs_whose_CoR_has_been_cancelled_by_the_RBI.XLSX` (from `https://www.rbi.org.in/scripts/BS_NBFCList.aspx`)
- **How downloaded**: Downloaded by hand from rbi.org.in as `api/data/raw/rbi_cancelled_nbfc.xlsx`
- **Download date**: 2026-11-14
- **Source date**: 2026-09-30
- **Row count**: 6,738 rows
- **Columns**: `name,website,list_name,source_type,source_url,source_date,note`
- **Exclusions**:
  - *(a) Record sheet (CoR restored)*: 12 excluded
  - *(b) Key matches currently registered NBFC / former name*: 27 excluded
  - *(c) Key shorter than 4 characters*: 3 excluded
- **Cleaning**: Extracted cancellation order dates / reference notes out of company names, trimmed whitespace.
