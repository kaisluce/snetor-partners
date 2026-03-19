# affacturage Data Dictionary

## Sources

### `BP_BUT000.csv` via `importBUT00.py`
- Selected positions: `0`, `7`, `11`, `12`
- Temporary columns:
  - `BP`
  - `Name`
  - `Last Name`
  - `First Name`
- Returned columns after person filter:
  - `BP`
  - `Name`

### `BP_KNB1.csv` via `importKNB1.py`
- Selected positions: `0`, `1`, `3`, `4`, `7`
- Returned columns:
  - `Customer`
  - `Company Code`
  - `Created On`
  - `Created by`
  - `AR Pledging Ind.`

## Final export schema

### `01_affacturage_full.xlsx`
### `02_affacturage_issues.xlsx`
- Main columns:
  - `Customer`
  - `Company Code`
  - `Created On`
  - `Created by`
  - `AR Pledging Ind.`
  - `Name`
  - `AR Planning Diag`
  - `In BUT00`
