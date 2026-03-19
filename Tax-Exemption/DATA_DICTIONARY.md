# Tax-Exemption Data Dictionary

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

## Final export schema

### `tax_exemption_data.xlsx`
- Pivot columns:
  - `BP`
  - `SalesOrg`
  - `Name`
  - `country`
  - `BP Country`
  - `Creation date`
  - `Created by`
  - `MWST`
  - `LCFR`

### `tax_exemption_results.xlsx`
### `missing_exemption_files.xlsx`
- Same columns as `tax_exemption_data.xlsx` plus:
  - `Has dispense file`
  - `Has attestation file`
