# reformateName Data Dictionary

## Source

### User-selected `.xlsx` file
- Loaded as-is by `import_base_dataset.py`
- No fixed input schema is enforced by the loader
- At runtime the user chooses:
  - one ID column
  - one or more name columns to concatenate
  - a max length for generated name segments

## Derived working columns
- `Name`: concatenation of the user-selected name columns
- `Name 1 updated`, `Name 2 updated`, ...:
  - generated on demand while splitting the concatenated name by the configured max length

## Final export schema

### `<input>_update.xlsx`
- Ordered columns:
  - the chosen ID column
  - generated `Name N updated` columns
  - the original chosen name columns
