# TaxClassification
Controle des pays / taxes par SalesOrg.
- Entrees: `KNVV`, `KNVI`, `BUT`, `BUT020`, `ADRC`, `Countries` (via scripts d'import)
- Sorties: dossier horodate sous `PATH` avec `tax_classification_full.xlsx`, `tax_classification_diag_ko.xlsx`
- Execution: `python main.py`
- Mail: envoi du fichier diag KO si anomalies
Ordre des taches:
1. Charger KNVV, KNVI, BUT, BUT020, ADRC et Countries.
2. Construire la table KV et diagnostiquer les anomalies taxes/pays.
3. Ecrire les rapports full/diag KO dans un dossier horodate.
4. Envoyer l'email si le diag KO n'est pas vide.
