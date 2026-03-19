# bp-enrisher Data Dictionary

## Main workflow
- The active enrichment flow is `from_extract.py`.
- It builds a French BP dataset, enriches missing tax identifiers, then exports a full file and a reduced file to edit.

## Sources

### `BP_BUT000.csv`
- Loaded with explicit headers in `from_extract.py`
- Key fields used:
  - `Business Partner`
  - `Grp.`
  - `Search Term 1`
  - `Name 1`
  - `Last Name`
  - `First Name`
  - `Date`
  - `User`

### `BP_BUT020.csv`
- Key fields used:
  - `Business Partner`
  - `Addr. No.`

### `BP_ADRC.csv`
- Key fields used after normalization:
  - `Addr. No.`
  - `street`
  - `street4`
  - `street5`
  - `city`
  - `postcode`
  - `country`

### `BP_TAXNUM.csv`
- Selected columns:
  - `BP`
  - `value`
  - `type`
- Pivoted output:
  - `VAT` from `FR0`
  - `siret` from `FR1`
  - `siren` from `FR2`

## Final export schema

### `frenchBPs.xlsx`
- Full working dataset before enrichment.

### `missing_siren_found.xlsx`
### `missing_siren_found_to_edit.xlsx`
- Exported columns:
  - `BP`
  - `Name 1`
  - `original missing siren`
  - `original missing siret`
  - `original missing vat`
  - `missing siren`
  - `missing siret`
  - `missing vat`
  - `matching siren`
  - `matching siret`
  - `matching vat`
  - `siren`
  - `siret`
  - `VAT`
  - `score`
  - `name score`
  - `street score`
  - `supposed right`
