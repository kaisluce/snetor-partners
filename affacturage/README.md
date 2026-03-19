# affacturage
Controle affacturage (AR pledging) pour clients KNB1.
- Entrees: `KVV`, `BUT00`, `KNB1` (via scripts d'import)
- Sortie: dossier horodate sous `\\snetor-docs\Users\MDM\998_CHecks\BP-AFFACTURAGE`
- Fichiers de sortie:
  - `01_affacturage_full.xlsx`
  - `02_affacturage_issues.xlsx`
  - log `.log` dans le meme dossier de run
- Email:
  - avec piece jointe si des issues existent
  - sans piece jointe si aucune issue
- Execution: `python \"main .py\"`
Ordre des taches:
1. Charger KVV, BUT00 et KNB1.
2. Construire le diagnostic AR Pledging (Missing/FF/autres).
3. Exporter les fichiers XLSX dans un dossier de run horodate.
4. Envoyer l'email de rapport.
