# CustomerType

Contrôle de l'Account Assignment Group (AAG) des clients par rapport au type attendu.

## Objectif

Pour chaque couple Client / SalesOrg dans KNVV, déterminer le type client attendu en fonction du pays de l'adresse et de la SalesOrg, puis comparer avec l'AAG renseigné dans SAP.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_KNVV.csv` | A=Customer, B=SalesOrg, C=Distribution Channel, D=Division, E=Created By, F=Created On, AL=Account Assgn. Grp. Current |
| `BP_BUT000.csv` | A=BP, F=Search Term 1, H=Name, L=Last Name, M=First Name |
| `BP_BUT020.csv` | A=BP, B=Addr. No. (adresse principale uniquement) |
| `BP_ADRC.csv` | A=Addr. No., L=BP Country |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#` (colonne `Name` et `Search Term 1`).
- BUT000 : exclut les personnes physiques (lignes où `Name` est vide mais `Last Name` ou `First Name` est renseigné).
- BUT020 : une seule adresse par BP (adresse principale = Addr. No. le plus grand).

## Jointures

```
KNVV --[Customer=BP]--> (left) BUT000
     --[Customer=BP]--> (left) BUT020 --[Addr. No.]--> (left) ADRC
```

## Mapping SalesOrg vers pays

| SalesOrg | Pays |
|---|---|
| FR11, FR12, FR13, FR14 | FR |
| GB11 | GB |

Toute SalesOrg absente de ce mapping provoque une erreur si `strict_salesorg_mapping=True` (valeur par défaut).

## Pays UE reconnus

`DE, AT, BE, BG, CY, HR, DK, ES, EE, FI, GR, IE, IT, LV, LT, LU, MT, NL, PL, PT, CZ, RO, SK, SI, SE, HU`

## Calcul du type attendu (ordre de priorité)

1. **Interco** : le nom du client contient une chaîne d'une entité SNETOR (SNETOR, OZYANCE, LEONARDI, etc.)
2. **SalesOrg inconnue** : SalesOrg absente du mapping → pas de type assigné
3. **Pays manquant** : `BP Country` vide → pas de type assigné
4. **Domestic** : pays du BP = pays de la SalesOrg
5. **UE** : pays du BP dans l'ensemble des pays UE
6. **Export** : tous les autres cas

## Mapping AAG attendu

| Type attendu | AAG attendu |
|---|---|
| Domestic | 1 |
| UE | 2 |
| Interco | 9 |
| Export | 3 |

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `Customer` | KNVV | Identifiant client |
| `SalesOrg` | KNVV | Organisation commerciale |
| `Name` | BUT000 | Dénomination |
| `Created By KNVV` | KNVV | Utilisateur créateur |
| `Creation Date KNVV` | KNVV | Date de création |
| `BP Country` | ADRC | Code pays de l'adresse principale |
| `Current type` | Calculé | Type correspondant à l'AAG actuel |
| `Account Assgn. Grp. Current` | KNVV | AAG renseigné dans SAP |
| `Expected type` | Calculé | Type attendu selon la logique métier |
| `Account Assgn. Grp. Expected` | Calculé | AAG attendu selon le type |
| `Account Assgn. Grp. Status` | Calculé | Diagnostic (voir ci-dessous) |

## Valeurs de diagnostic (`Account Assgn. Grp. Status`)

| Valeur | Condition |
|---|---|
| `OK` | AAG actuel = AAG attendu |
| `Missmatch` | AAG renseigné mais différent de l'attendu |
| `Missing country code` | `BP Country` vide |
| `Missing Asign. grp` | `Account Assgn. Grp. Current` vide |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-ACCOUNT_ASSIGNMENT\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `account_assignment_full.xlsx` | Toutes les lignes après filtres |
| `account_assignment_issues.xlsx` | Lignes où `Account Assgn. Grp. Status` != `OK` |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Customer Assignment` | `account_assignment_issues.xlsx` |
| Aucune issue | `Customer Assignment` | Aucune |
