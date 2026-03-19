# CustomerType
Controle du type client / account assignment (AK).
- Entrees: `KNVV`, `BUT000`, `BUT020`, `ADRC` (via scripts d'import)
- Sorties: dossier horodate sous `OUTPUT_ROOT` avec `account_assignment_full.xlsx`, `account_assignment_issues.xlsx`
- Execution: `python main.py`
- Mail: envoi automatique du fichier issues si present
- Note: `SALESORG_COUNTRY` doit etre complete pour le mode strict
Ordre des taches:
1. Charger KNVV, BUT000, BUT020 et ADRC.
2. Calculer le type attendu (Domestic/UE/Interco/Export) et comparer l'AK.
3. Generer les fichiers full/issues dans un dossier horodate.
4. Envoyer l'email si des issues sont presentes.
