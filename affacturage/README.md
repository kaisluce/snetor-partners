# affacturage

Contrôle de l'indicateur AR Pledging (affacturage) pour les clients enregistrés dans KNB1.

## Objectif

Vérifier que chaque client présent dans la table KNB1 possède bien l'indicateur AR Pledging (`AR Pledging Ind.`) positionné à `FF`. Toute valeur manquante ou incorrecte est signalée.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Chemin réseau | Colonnes extraites |
|---|---|---|
| `BP_BUT000.csv` | `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\` | A=BP, H=Name |
| `BP_KNB1.csv` | idem | A=Customer, B=Company Code, D=Created On, E=Created By, H=AR Pledging Ind. |

## Filtres appliqués

- Ne conserve que les clients dont l'identifiant commence par `1` (clients actifs).
- Exclut les noms commençant par `#` (entrées archivées).
- Exclut les entités interco SNETOR (correspondance exacte et `contains` sur les noms : SNETOR, OZYANCE, LEONARDI, etc.).
- Dédoublonnage sur `Customer` avant la jointure (une ligne par client dans KNB1 et BUT000).

## Jointure

```
KNB1 --[Customer]--> (left merge) <-- [Customer (renommé depuis BP)] -- BUT000
```

BUT000 est renommé `Customer` avant la jointure ; seules les colonnes `Customer` et `Name` sont conservées de BUT000.

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `Customer` | KNB1 | Identifiant client |
| `Company Code` | KNB1 | Code société |
| `Created On` | KNB1 | Date de création de la fiche KNB1 |
| `Created By` | KNB1 | Utilisateur créateur |
| `AR Pledging Ind.` | KNB1 | Valeur brute de l'indicateur |
| `Name` | BUT000 | Dénomination du BP |
| `AR Planning Diag` | Calculé | Diagnostic (voir ci-dessous) |
| `In BUT00` | Calculé | Booléen : le BP est-il présent dans BUT000 ? |

## Valeurs de diagnostic (`AR Planning Diag`)

| Valeur | Condition |
|---|---|
| `OK` | `AR Pledging Ind.` = `FF` |
| `Missing` | Champ vide |
| `Incorrect` | Valeur présente mais différente de `FF` |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-AFFACTURAGE\affacturage_check_YYYYMMDDHHMMSS\`

| Fichier | Contenu |
|---|---|
| `01_affacturage_full.xlsx` | Toutes les lignes après filtres |
| `02_affacturage_issues.xlsx` | Lignes où `AR Planning Diag` != `OK` ou `In BUT00` = False |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Missing AR Pledging FF` | `02_affacturage_issues.xlsx` |
| Aucune issue | `Missing AR Pledging FF` | Aucune |
