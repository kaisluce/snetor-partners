# findDROM Data Dictionary

## Sources

### `BP_BUT000.csv` via `importBUT000.py`
- Selected positions: `0`, `7`
- Returned columns:
  - `BP`
  - `Name`

### `BP_BUT020.csv` via `importBUT020.py`
- Selected positions: `0`, `1`
- Returned columns:
  - `BP`
  - `Addr. No.`

### `BP_ADRC.csv` via `importADRC.py`
- Returned columns:
  - `Addr. No.`
  - `street`
  - `street4`
  - `street5`
  - `city`
  - `postcode`
  - `country`

### Latest report via `importReport.py`
- The loader opens the latest report folder under `Z:\MDM\998_CHecks\BP-AUTOCHECKS`
- `BP` is normalized if present
- Optional fields used by `main.py` when available:
  - `siren`
  - `siret`
  - `VAT`
  - `Status`
  - alternative spellings of those fields are accepted

## Final export schema

### `FIND_DROM_<timestamp>.xlsx`
- Columns:
  - `BP`
  - `Name`
  - `Address`
  - `SIREN`
  - `SIRET`
  - `VAT`
  - `Status`
  - `Right country code`
