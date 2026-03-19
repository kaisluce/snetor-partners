# Address-Language Data Dictionary

## Sources

### `BP_BUT000.csv`
- Selected positions: `0`, `7`, `11`, `12`, `13`, `14`, `19`
- Returned columns:
  - `BP`
  - `Name`
  - `Last Name`
  - `First Name`
  - `Created On`
  - `Created By`
  - `Correspondence Language`
- Main filters:
  - drop empty `BP`
  - drop technical names starting with `#`
  - drop BPs starting with `9`, `5`, `29`
  - drop explicit BPs `10000010` and `10000012`
  - if `Name` is empty but `Last Name` / `First Name` exists, rebuild `Name` as `(person)...`

### `BP_BUT020.csv`
- Selected positions: `0`, `1`
- Returned columns:
  - `BP`
  - `Addr. No.`

### `BP_ADRC.csv`
- Selected positions: `0`, `11`, `19`, `26`, `27`, `28`, `29`, `20`
- Returned columns:
  - `Addr. No.`
  - `BP Country`
  - `Language`
  - `Street`
  - `Street 2`
  - `Street 3`
  - `Street 4`
  - `Street 5`

## Final export schema

### `language_street_full.xlsx`
### `street_issues.xlsx`
### `language_issues.xlsx`
- Columns:
  - `BP`
  - `Name`
  - `Last Name`
  - `First Name`
  - `Created By`
  - `Created On`
  - `Addr. No.`
  - `BP Country`
  - `Language`
  - `Street`
  - `Street 2`
  - `Street 3`
  - `Street 4`
  - `Street 5`
  - `Empty street 2 - 3?`
  - `Language diag`
