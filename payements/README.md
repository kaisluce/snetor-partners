# payements

Contrôle de la cohérence des conditions de paiement entre KNB1 (niveau société) et KNVV (niveau organisation commerciale) pour les clients.

## Objectif

Vérifier que les `Terms of Payment` renseignés dans KNB1 et dans KNVV sont identiques pour chaque couple Client / Société-SalesOrg. Toute divergence ou valeur manquante est signalée.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_KNB1.csv` | A=Customer, B=Company Code, D=Created By, E=Created On, G=Terms of Payment |
| `BP_KNVV.csv` | A=Customer, B=SalesOrg, E=Created By, F=Created On, AL=Terms of Payment KNVV |
| `BP_BUT000.csv` | A=BP (renommé Customer), H=Name |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#` (entrées archivées).
- BUT000 : agrégation des noms par Customer (jointure sur plusieurs lignes possible).

## Jointures

```
KNB1 --[Customer, Company Code = Customer, SalesOrg]--> (left merge) KNVV
     --[Customer]--> (left merge) BUT000
```

La jointure KNB1/KNVV associe `Company Code` (KNB1) à `SalesOrg` (KNVV) sur la même clé client.

## Logique de comparaison

- Les valeurs `NULL` sont remplacées par la chaîne `"Missing"` avant comparaison.
- `Terms Match` = `True` si les deux valeurs sont identiques ET non-manquantes.
- `Terms Match` = `"Missing"` si l'une ou l'autre valeur est absente.
- `Terms Match` = `False` si les deux valeurs sont présentes mais différentes.

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `Customer` | KNB1 | Identifiant client |
| `Name` | BUT000 | Dénomination du BP |
| `Company Code` | KNB1 | Code société |
| `SalesOrg` | KNVV | Organisation commerciale |
| `Created By` | KNB1 | Utilisateur créateur KNB1 |
| `Created On` | KNB1 | Date de création KNB1 |
| `Terms of Payment` | KNB1 | Conditions de paiement niveau société |
| `Terms of Payment KNVV` | KNVV | Conditions de paiement niveau ventes |
| `Terms Match` | Calculé | `True`, `False` ou `"Missing"` |

## Fichiers de sortie

Dossier horodaté créé sous `\\snetor-docs\Users\MDM\998_CHecks\BP-TERMS_OF_PAYMENT_CLIENT\YYYY-MM-DD_HH-MM-SS\`

| Fichier | Contenu |
|---|---|
| `payements.xlsx` | Toutes les lignes après filtres, triées par Customer puis Company Code |
| `payements_issue.xlsx` | Lignes où `Terms Match` != `True` (valeurs `False` ou `"Missing"`) |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Customer Terms of Payment` | `payements_issue.xlsx` |
| Aucune issue | `Customer Terms of Payment` | Aucune |
