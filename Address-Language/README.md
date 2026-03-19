# Address-Language
Petit controle des adresses BP: langue vs pays + champs rue.
- Entrees: `BP_BUT000.csv`, `BP_BUT020.csv`, `BP_ADRC.csv` (partage reseau)
- Sorties: dossier horodate sous `OUTPUT_ROOT` avec `language_street_full.xlsx`, `street_issues.xlsx`, `language_issues.xlsx`
- Execution: `python main.py`
- Mail: envoi automatique si anomalies detectees
Ordre des taches:
1. Charger BUT000, BUT020 et ADRC depuis le partage reseau.
2. Construire la table diagnostic (langue/pays et champs rue).
3. Ecrire les rapports XLSX dans un dossier horodate.
4. Envoyer les emails si des anomalies sont detectees.
