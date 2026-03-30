# SalesUser

Contrôle de la cohérence entre les utilisateurs commerciaux affectés à un BP (table USER_GPMSAL) et ceux attendus d'après le groupe de vente KNVV et la matrice de référence.

## Objectif

Pour chaque couple BP / SalesOrg, vérifier que les utilisateurs renseignés dans `USER_GPMSAL` correspondent exactement aux utilisateurs attendus selon le `Sales Group` et la `SalesGroupMatrix`.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_BUT000.csv` | BP, Name |
| `BP_KNVV.csv` | BP, SalesOrg, Sales Group, Created By, Created On |
| `BP_USER_GPMSAL.csv` | BP, Affected User |
| `SalesGroupMatrix.xlsx` | Sales Group, Affected User (plusieurs utilisateurs par groupe) |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#` (entrées archivées).
- Exclut les entités SNETOR.

## Jointures

```
KNVV --[BP]-----------> (left) BUT000
     --[Sales Group]--> (left) SalesGroupMatrix
     --[BP]-----------> (left) USER_GPMSAL (agrégation des utilisateurs par BP)
```

## Logique de comparaison

Pour chaque BP :

- `expected_users` = ensemble des utilisateurs définis dans `SalesGroupMatrix` pour le `Sales Group` du BP.
- `actual_users` = ensemble des utilisateurs présents dans `USER_GPMSAL` pour ce BP.
- Comparaison :
  - `missing users` = utilisateurs dans `expected_users` mais absents de `actual_users`.
  - `extra users` = utilisateurs dans `actual_users` mais absents de `expected_users`.

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `BP` | KNVV | Identifiant Business Partner |
| `Name` | BUT000 | Dénomination |
| `SalesOrg` | KNVV | Organisation commerciale |
| `Sales Group` | KNVV | Groupe de vente |
| `Created By KNVV` | KNVV | Utilisateur créateur |
| `Created On KNVV` | KNVV | Date de création |
| `Expected Users` | SalesGroupMatrix | Utilisateurs attendus (d'après la matrice) |
| `Actual Users` | USER_GPMSAL | Utilisateurs renseignés dans SAP |
| `Missing Users` | Calculé | Utilisateurs manquants |
| `Extra Users` | Calculé | Utilisateurs en trop |
| `Status` | Calculé | Diagnostic (voir ci-dessous) |

## Valeurs de diagnostic (`Status`)

| Valeur | Condition |
|---|---|
| `OK` | `expected_users` = `actual_users` |
| `missing users` | Des utilisateurs attendus ne sont pas dans GPMSAL |
| `extra users` | Des utilisateurs GPMSAL ne sont pas dans la matrice |
| `No Sales Group and no GPMSAL user` | Ni Sales Group ni utilisateur GPMSAL renseigné |

## Fichiers de sortie

Générés dans un dossier horodaté sous `\\snetor-docs\Users\MDM\998_CHecks\BP-SALES_USER\`

| Fichier | Contenu |
|---|---|
| `01_sales_user_consistency_full.xlsx` | Toutes les lignes après filtres |
| `02_sales_user_consistency_issue.xlsx` | Lignes où `Status` != `OK` |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Sales User` | `02_sales_user_consistency_issue.xlsx` |
| Aucune issue | `Sales User` | Aucune |
