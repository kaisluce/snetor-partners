# ON-Going-Check Data Dictionary

## Sources

### `BP_BUT000.csv` via `importBUT00.py`
- Returned columns after normalization and person filter:
  - `Bp`
  - `Group`
  - `Name 1`
  - `Name 2`
  - `Name 3`
  - `Name 4`
  - `Decreator`
  - `Creation date`

### On Going Screening source via `Import_onGoingScreen.py`
- Kept columns:
  - `Case id`
  - `Case name`
  - `Case rating`
  - `Case created date`
  - `Last screened date`

### B1 partner changes via `importB1data.py`
- Source: SQL stored procedure `SNE_Partners_Changes_Log`
- Returned columns are dynamic from SQL plus:
  - `source_database`
- The main script expects at least:
  - `Code Partenaire`
  - `Nom Partenaire`
  - `Traitement`
  - `Date Traitement`
  - `Utilisateur`

### Previous report via `latest_report.py`
- Used only for carry-over ignore lists and comparison context.

## Final export schema

### `results.xlsx`
### `results_with_folder.xlsx`
### `results_B1.xlsx`
### `results_B1_with_folder.xlsx`
- Intermediate run files; schemas depend on the merge path.

### `compliance_checked.xlsx`
### `issue_on_compliance.xlsx`
- Reindexed final columns:
  - `Bp`
  - `Name`
  - `Creation date`
  - `Decreator`
  - `Group`
  - `Traitement`
  - `Date Traitement`
  - `Utilisateur`
  - `source_database`
  - `Case Name`
  - `Case created date`
  - `Compliance folder`
  - `Has compliance folder`
  - `Missing Screen`
  - `Multiple Screens`
  - `valid creation date`
  - `Wrong On Going Check`
  - `Names To Ignore`
  - `Wrong compliance folder`
  - `Folder to Ignore`
