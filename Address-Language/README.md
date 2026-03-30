# Address-Language

Contrôle de la cohérence langue/pays et de la complétude des champs rue pour tous les Business Partners.

## Objectif

Vérifier que :

1. La langue SAP configurée sur l'adresse correspond au pays du BP (francophone → `F`, autres → `E`).
2. Les champs Street 2 et Street 3 sont vides (convention interne : la rue doit être dans Street).
3. Pour les BP belges (`BE`), la langue est détectée automatiquement via la bibliothèque `lingua` sur les champs rue.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Chemin réseau | Colonnes extraites |
|---|---|---|
| `BP_BUT000.csv` | `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\` | A=BP, H=Name, L=Last Name, M=First Name, N=Created On, O=Created By, T=Correspondence Language |
| `BP_BUT020.csv` | idem | A=BP, B=Addr. No. |
| `BP_ADRC.csv` | idem | A=Addr. No., L=BP Country, T=Language, U=Street 5, AA=Street, AB=Street 2, AC=Street 3, AD=Street 4 |

## Filtres appliqués sur BUT000

- BP vide exclu
- Name commençant par `#` exclu
- BP commençant par `9`, `5` ou `29` exclu
- BP `10000010` et `10000012` exclus
- Personnes physiques (Last Name / First Name renseignés sans Name) : reconstitution du nom `(person) NOM PRENOM` ; exclus si le nom contient `#`

## Jointures

```
BUT000 --[BP]--> (left merge) <-- [BP] -- BUT020 --[Addr. No.]--> (outer merge) <-- [Addr. No.] -- ADRC
```

- BUT020 : seule l'adresse principale est conservée (Addr. No. le plus grand par BP).
- Pour les personnes physiques, la langue utilisée est la colonne `Correspondence Language` (BUT000) et non `Language` (ADRC).

## Pays francophones reconnus

`FR, LU, MC, MQ, HT, SN, CI, BF, DZ, BJ, TG, ML, NE, GN, CM, GA, CG, CD, CF, TD, DJ, KM, MG, BI, RW, VU, SC, MA, TN, RE, YT, GF, MR`

## Colonnes de sortie

| Colonne | Description |
|---|---|
| `BP` | Identifiant Business Partner |
| `Name` | Nom (ou `(person) NOM PRENOM` pour les personnes) |
| `Last Name` | Nom de famille |
| `First Name` | Prénom |
| `Created By` | Utilisateur créateur |
| `Created On` | Date de création |
| `Addr. No.` | Numéro d'adresse principale |
| `BP Country` | Code pays de l'adresse |
| `Language` | Code langue SAP (`F`, `E`, …) |
| `Street` | Rue principale |
| `Street 2` | Complément rue 2 |
| `Street 3` | Complément rue 3 |
| `Street 4` | Complément rue 4 |
| `Street 5` | Complément rue 5 |
| `Empty street 2 - 3?` | Diagnostic rue : `OK`, `Not empty`, `No address found` |
| `Language diag` | Diagnostic langue : voir valeurs ci-dessous |
| `Expected language` | Langue attendue issue du rapport précédent (override manuel) |

## Valeurs de diagnostic

### `Language diag`

| Valeur | Signification |
|---|---|
| `OK` | Langue conforme au pays |
| `Wrong Language` | Langue incorrecte vs pays |
| `Empty language` | Champ langue vide |
| `No address found` | Aucune adresse trouvée pour ce BP |
| `No street found for BE diag` | BP belge sans champ rue renseigné (détection lingua impossible) |
| `No language detected with street` | `lingua` n'a pas pu déterminer la langue des champs rue (BP belge) |

### `Empty street 2 - 3?`

| Valeur | Signification |
|---|---|
| `OK` | Street 2 et Street 3 vides |
| `Not empty` | Au moins un des deux champs est renseigné |
| `No address found` | Pas d'adresse pour ce BP |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-LANGUAGE_AND_STREET_CHECK\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `language_street_full.xlsx` | Rapport complet (toutes lignes) |
| `street_issues.xlsx` | Lignes où `Empty street 2 - 3?` != `OK` |
| `language_issues.xlsx` | Lignes où `Language diag` != `OK` |

## Emails envoyés

| Sujet | Condition | Pièce jointe |
|---|---|---|
| `Address Street Check` | Issues rue présentes | `street_issues.xlsx` |
| `Address Street Check` | Aucune issue rue | Aucune |
| `Address Language Check` | Issues langue présentes | `language_issues.xlsx` |
| `Address Language Check` | Aucune issue langue | Aucune |

## Override de langue

Au démarrage, le script charge le rapport complet (`language_street_full.xlsx`) de la dernière exécution. Si la colonne `Expected language` est renseignée pour un BP, elle prime sur la logique automatique pour le calcul du `Language diag`.
