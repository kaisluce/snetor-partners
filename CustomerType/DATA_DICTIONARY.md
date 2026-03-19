# CustomerType Data Dictionary

## Sources

### `BP__KNVV.csv` via `importKNVV.py`
- Selected positions: `0`, `1`, `2`, `3`, `4`, `5`, `36`
- Returned columns:
  - `Customer`
  - `SalesOrg`
  - `DistributionChannel`
  - `Division`
  - `Created By KNVV`
  - `Creation Date KNVV`
  - `Account Assgn. Grp. Current`

### `BP_BUT000.csv` via `importBUT000.py`
- Selected positions: `0`, `5`, `7`, `11`, `12`
- Returned columns after person filter:
  - `BP`
  - `Search Term 1`
  - `Name`

### `BP_BUT020.csv` via `importBUT020.py`
- Selected positions: `0`, `1`
- Returned columns:
  - `BP`
  - `Addr. No.`

### `BP_ADRC.csv` via `importADRC.py`
- Selected positions: `0`, `11`
- Returned columns:
  - `Addr. No.`
  - `BP Country`

## Final export schema

### `account_assignment_full.xlsx`
### `account_assignment_issues.xlsx`
- Columns:
  - `Customer`
  - `SalesOrg`
  - `Name`
  - `Created By KNVV`
  - `Creation Date KNVV`
  - `BP Country`
  - `Current type`
  - `Account Assgn. Grp. Current`
  - `Expected type`
  - `Account Assgn. Grp. Expected`
  - `Account Assgn. Grp. Status`
