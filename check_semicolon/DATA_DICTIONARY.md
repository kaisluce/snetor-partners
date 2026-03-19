# check_semicolon Data Dictionary

## Sources

### `EXPORT_BUT000.xlsx` via `importBUT000.py`
- Local workbook stored in the project folder.
- The raw workbook is kept as-is.
- Standardized columns added by the loader:
  - `BP` from column index `0`
  - `Addr. No.` from column index `81`

### `BP_BUT020.csv` via `importBUT020.py`
- Selected positions: `0`, `1`
- Returned columns:
  - `BP`
  - `Addr. No.`

### `EXPORT_ADRC.xlsx` via `importADRC.py`
- Local workbook stored in the project folder.
- The raw workbook is kept as-is.
- Standardized column added by the loader:
  - `Addr. No.` from column index `0`

## Merged dataset
- `build_merged_df()` joins:
  - `BUT000` on `BP`
  - `BUT020` and `ADRC` on `Addr. No.`
- Output keeps the original workbook columns and renames address ids to:
  - `Addr. No. BUT000`
  - `Addr. No. BUT020`

## Issue export schema

### `special_char_issues_<timestamp>.xlsx`
- Same columns as the merged dataset
- Additional column:
  - `where`: comma-separated list of columns containing `;` or `"`
