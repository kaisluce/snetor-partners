# CreditVue Data Dictionary

## Sources

### `BP_UKM.csv` via `importUKM.py`
- Selected positions: first 2 columns
- Returned columns:
  - `Customer`
  - `Company Code`
- Important:
  - `Limit Valid To` is mentioned in comments but is not populated by the current loader.

### `BP_KNB1.csv` via `importKNB1.py`
- Selected positions: `0`, `4`, `3`, `1`
- Returned columns:
  - `Customer`
  - `Created By KNB1`
  - `Created On KNB1`
  - `Company Code`

### `BP_BUT000.csv` via `importBUT00.py`
- Selected positions: `0`, `7`, `11`, `12`
- Returned columns after person filter:
  - `Customer`
  - `Name`

## Final export schema

### `01_customer_vue_full.xlsx`
### `02_customer_vue_issues.xlsx`
- Main columns:
  - `Customer`
  - `Name`
  - `Company Code`
  - `Created By KNB1`
  - `Created On KNB1`
  - `Present in UKM`
  - `Present in KNB1`
  - `Diag`
