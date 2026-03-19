# TaxClassification Data Dictionary

## Sources

### `BP__KNVV.csv` via `importKNVV.py`
- Returned columns:
  - `BP`
  - `SalesOrg`

### `BP__KNVI.csv` via `importKNVI.py`
- Returned columns:
  - `ID`
  - `country`
  - `Cond type`
  - `Tax indicator`
  - `Key`

### `BP_BUT000.csv` via `importBUT.py`
- Selected positions: `0`, `7`, `11`, `12`, `13`, `14`
- Returned columns after person filter:
  - `BP`
  - `Name`
  - `Creation date`
  - `Created by`

### `BP_BUT020.csv` via `importBUT020.py`
- Returned columns:
  - `BP`
  - `Addr. No.`

### `BP_ADRC.csv` via `importADRC.py`
- Returned columns:
  - `Addr. No.`
  - `BP Country`

### Local countries workbook via `importCountries.py`
- Returned columns:
  - `SalesOrg`
  - `Plant`
  - `Country`

## Final export schema

### `tax_classification_full.xlsx`
### `tax_classification_diag_ko.xlsx`
- Output columns:
  - `BP`
  - `Name`
  - `Creation date`
  - `Created by`
  - `Addr. No.`
  - `BP Country`
  - `SalesOrg`
  - `Country Diag`
  - `Missing Countries`
  - `Missing LCFR`
  - `Missing LCIT`
  - `Empty Tax Indicator`
  - `MWST=0`
  - `MWST=0 LCFR!=1`
  - `LCIT=1`
  - `LCFR=1`
  - `MWST=0 FR`
  - `Tax Diag`
