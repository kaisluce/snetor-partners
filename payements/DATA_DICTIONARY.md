# payements Data Dictionary

## Sources

### Local `afacturage/KNB1.xlsx` via `importKNB1.py`
- Returned columns:
  - `Customer`
  - `Created By KNB1`
  - `Created On KNB1`
  - `Company Code`
  - `Terms of Payment`
  - `partner_id_org_com`

### `BP__KNVV.csv` via `importKNVV.py`
- Selected positions: `0`, `1`, `4`, `5`, `37`
- Returned columns:
  - `Customer`
  - `SalesOrg`
  - `Created By KNVV`
  - `Created On KNVV`
  - `Terms of Payment KNVV`
  - `partner_id_org_com`

### `BP_BUT000.csv` via `importBUT00.py`
- Selected positions: `0`, `7`, `11`, `12`
- Returned columns after person filter:
  - `Customer`
  - `Name`

## Final export schema

### `PAYEMENTS_<timestamp>.xlsx`
- Main columns produced by the merge:
  - `Customer`
  - `Name`
  - `Company Code`
  - `Created By KNB1`
  - `Created On KNB1`
  - `Terms of Payment`
  - `SalesOrg`
  - `Created By KNVV`
  - `Created On KNVV`
  - `Terms of Payment KNVV`
  - `partner_id_org_com`
  - `Terms Match`
