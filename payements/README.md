# payements
Controle des conditions de paiement KNB1 vs KNVV.
- Entrees: `KNB1`, `KNVV`, `BUT00` (via scripts d'import)
- Sortie: `PAYEMENTS_YYYYMMDD_HHMMSS.xlsx` dans le dossier courant
- Execution: `python main.py`
Ordre des taches:
1. Charger KNB1, KNVV et BUT00.
2. Fusionner les donnees et comparer les terms of payment.
3. Exporter le fichier XLSX.
