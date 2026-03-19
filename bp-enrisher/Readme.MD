# Find by name - BP Enrichment

## Purpose
This project enriches French Business Partners (BP) by completing missing identifiers (SIREN, SIRET, VAT).
It combines SAP exports, public APIs, and similarity scoring to infer SIREN/SIRET/VAT values.
It produces structured output files and can email a report when changes are detected.

## Data foundations

### Input files (SAP exports)
The paths are defined in `from_extract.py`:
- `BUT_000`: `BP_BUT000.csv`
- `BUT_020`: `BP_BUT020.csv`
- `ADRC`: `BP_ADRC.csv`
- `CREDS`: `BP_TAXNUM.csv`

These files are ingested and normalized (identifier coercion, French BP filtering, etc.).

### Endpoints used
- Company search (French government API):
  - Search: `https://recherche-entreprises.api.gouv.fr/search`
  - Near point: `https://recherche-entreprises.api.gouv.fr/near_point`
- Address geocoding (API Adresse):
  - `https://api-adresse.data.gouv.fr/search`
- SIRENE (avis de situation):
  - `https://api-avis-situation-sirene.insee.fr/identification/siren/{siren}?telephone=`
- Email delivery via Microsoft Graph (if enabled):
  - credentials in `config.cfg` and certificate `MDMPythonGraphV2.pfx`

### Algorithms and logic
- Normalization:
  - `format.py` cleans names, postcodes, and address components.
  - `from_extract.py` coerces identifier columns to text and normalizes values.
- SIREN/SIRET lookup:
  - `enrish_bp.py` attempts in order: postcode, departement, name-only, then coordinate search.
  - `get_best_match.py` computes a combined score (name + address) using `thefuzz`.
- VAT enrichment:
  - `calculate_Vat` computes a French VAT from a SIREN.
- SIRET via SIRENE:
  - `requestFromSiren.py` queries the SIRENE API and selects the closest establishment by address.

## Outputs
A timestamped run directory is created under `OUTPUT_DIR`:
- `frenchBPs.xlsx`: filtered dataset prior to enrichment
- `missing_siren_found.xlsx`: full enriched dataset
- `missing_siren_found_to_edit.xlsx`: only corrected rows

Logs:
- `logs/YYYY-MM-DD_HH-MM_LOG.log`

Email:
- `emailing.py` sends a report when `edited_file` contains changes

## Quick guide: where to change endpoints
- Company search (search): `recherche_soc_api.py` -> `API_URL`
- Company search (near_point): `request_by.py` -> `request_by_coordinates` (param `url`)
- Address geocoding: `recherche_cord.py` -> `url`
- SIRENE: `requestFromSiren.py` -> `url` construction
- Graph email: `config.cfg` (clientId/tenantId/certificate)

## Run a job
- `python from_extract.py`

If necessary, adjust SAP paths or the endpoints above, then re-run.
