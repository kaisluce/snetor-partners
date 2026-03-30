# CreditVue

Contrôle de la cohérence entre la vue crédit (UKM) et les fiches clients KNB1.

## Objectif

Identifier les écarts entre la table UKM (credit view SAP) et la table KNB1 (fiche comptable client) :

- Clients présents dans KNB1 mais absents de l'UKM → `missing credit vue`
- Clients présents dans l'UKM mais absents de KNB1 → `missing knb1 entry`

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_UKM.csv` | Customer, Company Code, Limit Valid To |
| `BP_KNB1.csv` | Customer, Company Code, Created By, Created On |
| `BP_BUT000.csv` | BP (renommé Customer), Name |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#` (entrées archivées).
- Exclut les entités interco SNETOR (correspondance par `contains` sur le nom en majuscules).
- Ne conserve que les clients dont l'identifiant commence par `1`.
- Ne conserve que les clients dont l'identifiant fait exactement 7 caractères.

## Jointures

```
UKM --[Customer, Company Code]--> (outer merge) <-- [Customer, Company Code] -- KNB1
        résultat --[Customer]--> (left merge) <-- [Customer] -- BUT000
```

La jointure UKM/KNB1 est en `outer` pour détecter les absences des deux côtés. La jointure BUT000 est en `left` pour enrichir avec le nom.

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `Customer` | UKM / KNB1 | Identifiant client |
| `Name` | BUT000 | Dénomination du BP |
| `Company Code` | UKM / KNB1 | Code société |
| `Limit Valid To` | UKM | Date de validité de la limite de crédit |
| `Created By KNB1` | KNB1 | Utilisateur créateur de la fiche KNB1 |
| `Created On KNB1` | KNB1 | Date de création de la fiche KNB1 |
| `Present in UKM` | Calculé | Booléen : ligne présente dans UKM |
| `Present in KNB1` | Calculé | Booléen : ligne présente dans KNB1 |
| `Diag` | Calculé | Diagnostic (voir ci-dessous) |

## Valeurs de diagnostic (`Diag`)

| Valeur | Condition |
|---|---|
| `OK` | Client présent dans UKM et KNB1 |
| `missing knb1 entry` | Présent dans UKM, absent de KNB1 |
| `missing credit vue` | Présent dans KNB1, absent de UKM |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-CREDIT_VUE\customer_vue_check_YYYYMMDDHHMMSS\`

| Fichier | Contenu |
|---|---|
| `01_customer_vue_full.xlsx` | Toutes les lignes après filtres |
| `02_customer_vue_issues.xlsx` | Lignes où `Diag` != `OK` (généré uniquement si issues) |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Credit Vue` | `02_customer_vue_issues.xlsx` |
| Aucune issue | `Credit Vue` | Aucune |
