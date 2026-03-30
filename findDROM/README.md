# findDROM

Détection des Business Partners situés dans les départements et régions d'outre-mer français (DROM), et vérification de la cohérence du code pays SAP.

## Objectif

Identifier les BP dont l'adresse correspond à un DROM (Réunion, Guadeloupe, Martinique, Guyane, Mayotte, etc.) selon plusieurs critères : code pays, code postal et ville. Vérifier que le code pays SAP est bien le code DOM/TOM attendu et non `FR`.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_BUT000.csv` | A=BP, H=Name |
| `BP_BUT020.csv` | A=BP, B=Addr. No. |
| `BP_ADRC.csv` | Addr. No., Street, Street 4, Street 5, City, Postcode, BP Country |
| Dernier rapport AUTOCHECK (`\\snetor-docs\Users\MDM\998_CHecks\BP-AUTOCHECKS\`) | SIREN, SIRET, VAT, Status (optionnel) |

## Filtres appliqués

Un BP est considéré comme DROM si au moins une des conditions suivantes est vraie :

- `BP Country` dans `{RE, GP, MQ, YT, GF, BL, MF, PM, WF, PF}`
- Préfixe du code postal dans `{971, 972, 973, 974, 975, 976, 986, 987}`
- Ville dans la liste des villes DROM connues (ex : Pointe-à-Pitre, Fort-de-France, Saint-Denis de la Réunion, Cayenne, Mamoudzou, etc.)

## Jointures

```
BUT000 --[BP]--> (left) BUT020 --[Addr. No.]--> (left) ADRC
       --[BP]--> (left) Dernier rapport AUTOCHECK
```

## Vérification de cohérence pays/code postal

Pour chaque DROM, le code pays attendu est :

| Territoire | Code pays attendu | Préfixe postal |
|---|---|---|
| La Réunion | RE | 974 |
| Guadeloupe | GP | 971 |
| Martinique | MQ | 972 |
| Guyane | GF | 973 |
| Mayotte | YT | 976 |
| Saint-Pierre-et-Miquelon | PM | 975 |
| Polynésie française | PF | 987 |
| Wallis-et-Futuna | WF | 986 |

La colonne `Right country code` indique si le code pays SAP correspond au préfixe postal détecté.

## Colonnes de sortie

| Colonne | Description |
|---|---|
| `BP` | Identifiant Business Partner |
| `Name` | Dénomination |
| `Street` | Adresse construite (concaténation des champs rue) |
| `City` | Ville |
| `Postcode` | Code postal |
| `BP Country` | Code pays SAP actuel |
| `SIREN` | Numéro SIREN (si disponible depuis le rapport AUTOCHECK) |
| `SIRET` | Numéro SIRET |
| `VAT` | Numéro TVA |
| `Status` | Statut depuis le rapport AUTOCHECK |
| `Right country code` | Booléen : le code pays correspond au DROM détecté |

## Fichier de sortie

| Fichier | Contenu |
|---|---|
| `FIND_DROM_YYYYMMDD_HHMMSS.xlsx` | Tous les BP identifiés comme DROM |
