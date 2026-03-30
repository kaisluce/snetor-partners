# TaxClassification

Contrôle de la classification fiscale (MWST, LCFR, LCIT) par combinaison BP / SalesOrg / Pays.

## Objectif

Pour chaque couple BP / SalesOrg, vérifier que :

1. Tous les pays attendus pour cette SalesOrg ont bien une ligne MWST.
2. Si le pays `FR` est dans le périmètre, une ligne LCFR existe.
3. Si le pays `IT` est dans le périmètre, une ligne LCIT existe.
4. Aucun indicateur fiscal n'est vide.
5. MWST=0 en France implique LCFR=1 (cas d'exemption de TVA).
6. MWST=0 hors France est signalé comme anomalie.
7. LCIT=1 est signalé comme anomalie.
8. LCFR=1 hors contexte d'exemption est signalé.

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
| `Countries.xlsx` | SalesOrg, Plant, Country (périmètre pays par SalesOrg) |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#`.
- Exclut les pays `GR`, `AE`, `HR` de KNVI et de Countries (pays ignorés du périmètre).

## Jointures

```
KNVV --[BP=ID]--> (left) KNVI
     --[BP]-----> (left) BUT000
     --[BP]-----> (left) BUT020 --[Addr. No.]--> (left) ADRC
```

Le résultat est regroupé par `(BP, SalesOrg)` pour construire une ligne de diagnostic par couple.

## Logique de diagnostic par couple (BP, SalesOrg)

**Étape 1 — Pays manquants**

- `exp_set` = ensemble des pays attendus pour cette SalesOrg (depuis Countries.xlsx).
- `act_set` = ensemble des pays avec une ligne MWST dans KNVI pour ce BP/SalesOrg.
- Si `exp_set - act_set` non vide → `Country Diag = "Missing one or many countries"`, sinon `"ok"`.

**Étape 2 — Lignes de condition manquantes**

- Pour chaque pays `FR` dans `exp_set` : si aucune ligne `LCFR` n'existe → diagnostic `"Missing LCFR line"`.
- Pour chaque pays `IT` dans `exp_set` : si aucune ligne `LCIT` n'existe → diagnostic `"Missing LCIT line"`.

**Étape 3 — Indicateurs vides**

- Si au moins un `Tax indicator` est vide → `"Missing one or many tax indicator"`.

**Étape 4 — Indicateurs MWST/LCFR/LCIT**

- Pays `FR` : si MWST=0 et LCFR!=1 → `"MWST = 0 and LCFR != 1"`.
- Pays `FR` : si MWST=0 et LCFR=1 → cas d'exemption valide (`MWST=0 FR=True`, `LCFR=1=True`).
- Autre pays : si MWST=0 → `"One or many countries have MWST = 0"`.
- Autre pays : si LCFR=1 → `"LCFR = 1"`.
- Si LCIT=1 → `"LCIT = 1"`.

## Colonnes de sortie

| Colonne | Description |
|---|---|
| `BP` | Identifiant Business Partner |
| `Name` | Dénomination |
| `Creation date` | Date de création |
| `Created by` | Utilisateur créateur |
| `Addr. No.` | Numéro d'adresse principale |
| `BP Country` | Pays de l'adresse principale |
| `SalesOrg` | Organisation commerciale |
| `Country Diag` | `"ok"` ou `"Missing one or many countries"` |
| `Missing Countries` | Liste des pays manquants (séparés par virgule) |
| `Missing LCFR` | Booléen : ligne LCFR absente pour FR |
| `Missing LCIT` | Booléen : ligne LCIT absente pour IT |
| `Empty Tax Indicator` | Booléen : au moins un indicateur vide |
| `MWST=0` | Booléen : MWST=0 sur un pays hors FR |
| `MWST=0 LCFR!=1` | Booléen : MWST=0 en FR sans LCFR=1 |
| `LCIT=1` | Booléen : LCIT positionné à 1 |
| `LCFR=1` | Booléen : LCFR positionné à 1 (hors exemption) |
| `MWST=0 FR` | Booléen : MWST=0 en France (avec ou sans LCFR) |
| `Tax Diag` | Résumé textuel des diagnostics (virgule-séparé), `"OK"` si conforme |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-TAX_CLASSIFICATION\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `tax_classification_full.xlsx` | Toutes les lignes (inclut des lignes d'information sur les pays ignorés) |
| `tax_classification_diag_ko.xlsx` | Lignes où `Country Diag` != `"ok"` ou `Tax Diag` != `"OK"` |

> Note : le fichier full contient en fin de tableau des lignes spéciales signalant les pays ignorés (`GR`, `AE`, `HR`) et indiquant les numéros de lignes à supprimer dans `main.py` si le périmètre change.

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Tax Classification` | `tax_classification_diag_ko.xlsx` |
| Aucune issue | `Tax Classification` | Aucune |

## Dictionnaire de données complémentaire

Voir [DATA_DICTIONARY.md](DATA_DICTIONARY.md) pour le détail des colonnes par fichier source.
