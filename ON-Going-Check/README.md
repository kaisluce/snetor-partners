# ON-Going-Check

Contrôle de compliance on-going pour les Business Partners S4 et B1 : vérification de la présence d'un screening actif et d'un dossier de compliance réseau.

## Objectif

Pour chaque BP actif (S4 via BUT000, B1 via SQL) :

1. Trouver une correspondance dans la source de screening on-going (par nom exact ou fuzzy >= 90).
2. Vérifier qu'un dossier de compliance existe dans le répertoire réseau correspondant au groupe du BP.
3. Consolider les résultats S4 et B1 en un seul fichier de diagnostic.

## Installation

```powershell
cd ON-Going-Check
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Exécution

```powershell
py -3 main.py
```

## Fichiers d'entrée

| Fichier / Source | Description | Colonnes utilisées |
|---|---|---|
| `BP_BUT000.csv` | Données BP S4 | BP, Group, Name 1-4, Creation date, Decreator |
| Source screening (CSV/Excel) | Liste des cases on-going | Case id, Case name, Case rating, Case created date, Last screened date |
| SQL B1 | Modifications partenaires B1 (2 dernières semaines) | Code Partenaire, Nom Partenaire, Traitement, Date Traitement, Utilisateur |
| Dernier rapport (`results_with_folder.xlsx`) | Rapport de l'exécution précédente | BP, Wrong On Going Check, Compliance folder, Wrong compliance folder |
| `ignore_cases.json` | Cas à ignorer par BP (clé=BP) | Liste de noms de cases à exclure du matching |
| `ignore_folders.json` | Dossiers à ignorer par BP (clé=BP) | Liste de noms de dossiers à exclure |

Chemin des fichiers JSON : `\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\DO_NOT_DELETE\`

## Filtres appliqués sur BUT000

- Groupes conservés : `ZG01`, `ZG02`, `ZG03`, `ZG04`, `ZG05`, `ZG06`, `ZG07`, `ZG09`, `ZG13`
- Noms exclus : `#DO NOT USE`, `DO NOT USE`, `#DEFAULT`, `#DO NOT USE I.C.S.A`, `# DIVISION NE PAS UTILISER`
- Entités SNETOR exclues
- Noms de longueur <= 2 exclus

Filtres appliqués sur B1 : exclut les codes partenaires commençant par `FG` ou `FS`.

## Logique de matching screening (fonction `treat_line_partner`)

1. Récupère les noms à ignorer depuis `ignore_cases.json` pour ce BP.
2. Si le rapport précédent indique `Wrong On Going Check = True` pour ce BP, le `Case Name` précédent est ajouté aux noms à ignorer et sauvegardé dans le JSON.
3. Calcule le score fuzzy (`thefuzz.fuzz.token_set_ratio`) entre le nom du BP (en majuscules) et chaque `Case name` de la source screening.
4. Conserve les cases avec score >= 90 non présentes dans la liste d'ignorance.
5. Si plusieurs cases trouvées → `Multiple Screens = True`, prend la plus récente.
6. Si aucune case trouvée → `Missing Screen = True`.
7. `valid creation date = True` si la date de la case est dans les 3 dernières années.

## Logique de recherche dossier (fonction `look_for_folder`)

Mapping Groupe → dossier de compliance :

| Groupe | Dossier recherché |
|---|---|
| ZG01 | `001 Clients - Customers` puis `004 Fournisseurs - Suppliers` |
| ZG02 à ZG07 | `004 Fournisseurs - Suppliers` |
| ZG09 | `005 Fournisseurs Frais Généraux - General Expense Suppliers` |
| ZG13 | `002 Clients livre - Ship to Customers` |

Pour B1, le préfixe du code partenaire détermine le dossier (`CL` → Clients, `FB`/`FT`/`FA` → Fournisseurs).

La recherche utilise thefuzz (score >= 90) sur les noms de sous-dossiers. Les dossiers en erreur du rapport précédent sont ajoutés à `ignore_folders.json`.

Chemin de base compliance : `\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\1partner creation\`

## Colonnes de sortie (`compliance_checked.xlsx`)

| Colonne | Description |
|---|---|
| `Bp` | Identifiant BP |
| `Name` | Dénomination |
| `Creation date` | Date de création (S4 uniquement) |
| `Decreator` | Utilisateur créateur (S4) |
| `Group` | Groupe BP (S4) |
| `Traitement` | Type de mouvement (B1) |
| `Date Traitement` | Date du mouvement (B1) |
| `Utilisateur` | Utilisateur B1 |
| `source_database` | `S4` ou `B1` |
| `Case Name` | Nom du case on-going trouvé |
| `Case created date` | Date de création du case |
| `Compliance folder` | Chemin du dossier compliance trouvé |
| `Has compliance folder` | Booléen : dossier trouvé |
| `Missing Screen` | Booléen : aucun screening trouvé |
| `Multiple Screens` | Booléen : plusieurs screenings trouvés |
| `valid creation date` | Booléen : case datée dans les 3 dernières années |
| `Wrong On Going Check` | Valeur du rapport précédent (pour carry-over) |
| `Names To Ignore` | Noms de cases ignorés pour ce BP |
| `Wrong compliance folder` | Valeur du rapport précédent (pour carry-over) |
| `Folder to Ignore` | Dossiers ignorés pour ce BP |

## Critères d'inclusion dans les issues

Une ligne est incluse dans `issue_on_compliance.xlsx` si :

- `Has compliance folder = False`, OU
- `Missing Screen = True`, OU
- `Multiple Screens = True`, OU
- `valid creation date = False`

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `results.xlsx` | Résultats screening S4 (avant vérification dossier) |
| `results_with_folder.xlsx` | Résultats S4 avec vérification dossier |
| `results_B1.xlsx` | Résultats screening B1 (avant vérification dossier) |
| `results_B1_with_folder.xlsx` | Résultats B1 avec vérification dossier |
| `compliance_checked.xlsx` | Consolidation S4 + B1 (toutes lignes) |
| `issue_on_compliance.xlsx` | Lignes avec au moins une anomalie |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `On Going Screen` | `issue_on_compliance.xlsx` |
| Aucune issue | `On Going Screen` | Aucune |

## Logs

Fichiers log générés dans `ON-Going-Check/logs/`.
