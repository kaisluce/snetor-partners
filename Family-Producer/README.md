# Family-Producer

Découpe le dernier fichier EXPORT en deux datasets séparés : ZFAMILY et ZPRODUCER, et exporte uniquement si le contenu a changé depuis la dernière exécution.

## Objectif

À partir du dernier export brut `EXPORT_*.xlsx`, extraire les lignes correspondant aux caractéristiques `ZFAMILY` et `ZPRODUCER` et les sauvegarder dans des fichiers horodatés distincts, uniquement si leur contenu diffère du dernier fichier de sortie existant.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Description | Colonnes utilisées |
|---|---|---|
| `EXPORT_*.xlsx` (le plus récent) | Export brut de caractéristiques | Col 0 = type (ZFAMILY / ZPRODUCER), Col 1 = Internal char no., Col 2 = Int counter values, Col 3 = Int. counter |

Le script sélectionne automatiquement le fichier `EXPORT_*.xlsx` le plus récent par date de modification dans le dossier courant.

## Logique de traitement

1. Lecture du dernier `EXPORT_*.xlsx` (4 premières colonnes).
2. Filtrage sur la colonne 0 :
   - Valeur `"ZFAMILY"` → dataset famille.
   - Valeur `"ZPRODUCER"` → dataset producteur.
3. Comparaison avec le dernier fichier de sortie correspondant dans `outputs/` :
   - Si le contenu est identique → aucun fichier généré (pas de modification).
   - Si le contenu diffère → génération d'un nouveau fichier horodaté.
4. Journalisation via `logger.py`.

## Colonnes de sortie

Les 4 colonnes de l'export source sont conservées telles quelles (sans renommage) :

| Position | Contenu |
|---|---|
| 0 | Type caractéristique (`ZFAMILY` ou `ZPRODUCER`) |
| 1 | Internal char no. |
| 2 | Int counter values |
| 3 | Int. counter |

## Fichiers de sortie

Générés dans le sous-dossier `outputs/` uniquement si le contenu a changé :

| Fichier | Contenu |
|---|---|
| `ZFAMILY_updated_YYYYMMDD_HHMMSS.xlsx` | Lignes ZFAMILY du dernier export |
| `ZPRODUCER_updated_YYYYMMDD_HHMMSS.xlsx` | Lignes ZPRODUCER du dernier export |

## Logs

Messages émis via `logger.py` indiquant :
- Quel fichier EXPORT a été sélectionné.
- Si un fichier de sortie a été généré ou non (pas de changement détecté).
