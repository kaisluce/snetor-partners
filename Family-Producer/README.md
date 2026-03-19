# Family-Producer
Decoupe ZFAMILY / ZPRODUCER depuis le dernier export.
- Entree: dernier `EXPORT_*.xlsx` du dossier
- Sorties: `outputs/ZFAMILY_updated_*.xlsx` et `outputs/ZPRODUCER_updated_*.xlsx` si changement
- Execution: `python main.py`
- Log: messages via `logger.py`
Ordre des taches:
1. Selectionner le dernier `EXPORT_*.xlsx`.
2. Separarer les lignes ZFAMILY et ZPRODUCER.
3. Comparer avec les derniers outputs et ecrire si changement.
