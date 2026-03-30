# check_semicolon

Détection des caractères spéciaux problématiques (point-virgule `;` et guillemet `"`) dans les champs d'adresse des Business Partners, susceptibles de corrompre les exports CSV.

## Objectif

Identifier les BP dont les champs nom ou adresse contiennent un `;` ou un `"`, ce qui peut provoquer des erreurs de parsing dans les exports SAP au format CSV séparé par point-virgule.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes examinées |
|---|---|
| `BP_BUT000.csv` | BP, Name |
| `BP_BUT020.csv` | BP, Addr. No. |
| `BP_ADRC.csv` | Tous les champs d'adresse (Street, Street 2-5, City, Postcode, Country, etc.) |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Jointures

```
BUT000 --[BP]--> (left) BUT020 --[Addr. No.]--> (left) ADRC
```

## Logique de détection

1. Après jointure, chaque cellule textuelle est inspectée.
2. Une ligne est retenue si au moins un champ contient `;` ou `"`.
3. Une colonne `where` est ajoutée, listant les noms des colonnes concernées.

## Colonnes de sortie

Toutes les colonnes du DataFrame joint, plus :

| Colonne | Description |
|---|---|
| `where` | Noms des colonnes contenant le caractère problématique |

## Fichier de sortie

| Fichier | Contenu |
|---|---|
| `special_char_issues_YYYYMMDD_HHMMSS.xlsx` | Lignes avec au moins un `;` ou `"` dans les champs adresse |
