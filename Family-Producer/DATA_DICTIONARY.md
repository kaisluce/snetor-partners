# Family-Producer Data Dictionary

## Source

### Latest `EXPORT_*.xlsx`
- The script always picks the most recent workbook in the project folder.
- Selected positions: first 4 columns
- Standardized columns:
  - `Internal char no.`
  - `Int counter values`
  - `Int. counter`
  - `Characteristic Value`

## Derived datasets

### `ZFAMILY`
- Filter rule:
  - `Internal char no.` equals `ZFAMILY`

### `ZPRODUCER`
- Filter rule:
  - `Internal char no.` equals `ZPRODUCER`

## Outputs

### `outputs/ZFAMILY_updated_<timestamp>.xlsx`
### `outputs/ZPRODUCER_updated_<timestamp>.xlsx`
- Both outputs keep the same 4 standardized columns as the source slice.
