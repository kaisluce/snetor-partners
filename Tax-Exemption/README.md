# Tax-Exemption

Contrôle de la présence des documents justificatifs d'exemption de TVA pour les clients français avec MWST=0 et LCFR=1.

## Objectif

Identifier les clients français qui bénéficient d'une exemption de TVA (MWST=0 et LCFR=1) et vérifier que les documents requis sont présents dans le dossier source :

- `DECISION DE DISPENSE`
- `ATTESTATION FRANCHISE TVA`

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_KNVV.csv` | BP, SalesOrg |
| `BP_KNVI.csv` | ID (=BP), country, Cond type, Tax indicator |
| `BP_BUT000.csv` | BP, Name, Creation date, Created by |
| `BP_BUT020.csv` | BP, Addr. No. |
| `BP_ADRC.csv` | Addr. No., BP Country |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

Dossier des justificatifs : `\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\001_Customer\Exemption\`

## Filtres appliqués

- Exclut les noms commençant par `#` (entrées archivées).
- Ne conserve que les clients avec `BP Country = FR` (ou `country = FR` si BP Country manquant).
- Ne conserve que les lignes avec `Cond type` dans `{MWST, LCFR}`.
- Pivote sur `Cond type` et ne conserve que les lignes où `MWST = 0` ET `LCFR = 1`.

## Jointures

```
KNVV --[BP=ID]--> (left) KNVI
     --[BP]-----> (left) BUT000
     --[BP]-----> (left) BUT020 --[Addr. No.]--> (left) ADRC
```

## Logique de pivot et filtrage

1. Filtrage sur `BP Country = FR` et `Cond type` in `[MWST, LCFR]`.
2. Pivot : une ligne par `(BP, SalesOrg, Name, country, BP Country, Creation date, Created by)`, colonnes `MWST` et `LCFR` avec la valeur de `Tax indicator`.
3. Filtre final : `MWST = "0"` ET `LCFR = "1"`).

## Vérification des documents (fonction `check_files`)

Pour chaque ligne de la table pivotée :

1. Construction du chemin : `<base>/<année la plus récente>/<SalesOrg>/`
2. Parcours récursif de tous les fichiers du dossier.
3. Correspondance : le nom du fichier (en majuscules) contient le nom du client (en majuscules).
4. `Has dispense file = True` si un fichier contient `"DECISION DE DISPENSE"`.
5. `Has attestation file = True` si un fichier contient `"ATTESTATION FRANCHISE TVA"`.

L'année utilisée est toujours la plus récente disponible dans le dossier `Exemption/`.

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `BP` | KNVV | Identifiant client |
| `SalesOrg` | KNVV | Organisation commerciale |
| `Name` | BUT000 | Dénomination du BP |
| `country` | KNVI | Pays de la condition fiscale |
| `BP Country` | ADRC | Pays de l'adresse principale |
| `Creation date` | BUT000 | Date de création du BP |
| `Created by` | BUT000 | Utilisateur créateur |
| `MWST` | KNVI (pivoté) | Valeur de l'indicateur MWST |
| `LCFR` | KNVI (pivoté) | Valeur de l'indicateur LCFR |
| `Has dispense file` | Calculé | Booléen : fichier DECISION DE DISPENSE trouvé |
| `Has attestation file` | Calculé | Booléen : fichier ATTESTATION FRANCHISE TVA trouvé |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-TAX_EXEMPTION\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `tax_exemption_data.xlsx` | Table pivotée avant vérification des fichiers |
| `tax_exemption_results.xlsx` | Table avec colonnes `Has dispense file` et `Has attestation file` |
| `missing_exemption_files.xlsx` | Lignes où au moins un des deux documents est absent |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Documents manquants | `Tax Exemption` | `missing_exemption_files.xlsx` |
| Tous documents présents | `Tax Exemption` | Aucune |
