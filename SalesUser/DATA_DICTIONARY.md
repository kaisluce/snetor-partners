# SalesUser Data Dictionary

## Sources

### `BP__KNVV.csv` via `importKNVV.py`
- Selected positions: `0`, `1`, `4`, `5`, `39`
- Returned columns:
  - `BP`
  - `SalesOrg`
  - `Created By (KNVV)`
  - `Created On (KNVV)`
  - `Sales Group`

### `BP_BUT000.csv` via `importBUT00.py`
- Selected positions: `0`, `7`, `11`, `12`
- Returned columns after person filter:
  - `BP`
  - `Name`

### `BP_USER_GPMSAL.csv` via `importUSER_GPMSAL.py`
- Selected positions: `0`, `1`
- Returned columns:
  - `BP`
  - `Affected User`

### `Sales Group.xlsx` via `importSalesGroup.py`
- Selected positions: Excel columns `C` and `F`
- Returned columns:
  - `Sales Group`
  - `Affected User`

## Final export schema

### `01_sales_user_consistency_full.xlsx`
### `02_sales_user_consistency_issue.xlsx`
- Preferred exported columns:
  - `BP`
  - `Name`
  - `Created By (KNVV)`
  - `Created On (KNVV)`
  - `SalesOrg`
  - `Sales Group`
  - `Affected User`
  - `gpmsal users`
  - `missing users`
  - `extra users`
  - `No Sales Group and no GPMSAL user`
- Optional extra column added on error path:
  - `Consistency Check Error`
