# payment_supplier

Contrôle de la cohérence des conditions de paiement fournisseurs entre LFB1 (niveau société) et LFM1 (niveau site/matériel).

## Objectif

Vérifier que les `Terms of Payment` renseignés dans LFB1 et LFM1 sont identiques pour chaque fournisseur. Toute divergence ou valeur manquante est signalée.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_LFB1.csv` | Supplier, Company Code, Created On, Created By, Terms of Payment |
| `BP__LFM1.csv` | Supplier, Company Code, Created On, Created By, Terms of Payment |
| `BP_BUT000.csv` | BP (renommé Supplier), Name |

Chemin réseau commun : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Filtres appliqués

- Exclut les noms commençant par `#` (entrées archivées).

## Jointures

```
LFB1 --[Supplier, Company Code]--> (outer merge) <-- [Supplier, Company Code] -- LFM1
     --[Supplier]--> (left merge) <-- [Supplier] -- BUT000
```

La jointure LFB1/LFM1 est en `outer` pour détecter les absences des deux côtés.

## Logique de comparaison

| Valeur `Terms Match` | Condition |
|---|---|
| `True` | LFB1 et LFM1 ont la même valeur |
| `False` | Les deux valeurs sont présentes mais différentes |
| `"Missing LFB1 Term"` | LFM1 renseigné, LFB1 manquant |
| `"Missing LFM1 Term"` | LFB1 renseigné, LFM1 manquant |
| `"Missing LFB1 and LFM1 Terms"` | Les deux manquants |

## Colonnes de sortie

| Colonne | Source | Description |
|---|---|---|
| `Supplier` | LFB1 / LFM1 | Identifiant fournisseur |
| `Name` | BUT000 | Dénomination du BP |
| `Company Code` | LFB1 / LFM1 | Code société |
| `Created On LFB1` | LFB1 | Date de création LFB1 |
| `Created By LFB1` | LFB1 | Utilisateur créateur LFB1 |
| `Terms of Payment LFB1` | LFB1 | Conditions de paiement niveau société |
| `Created On LFM1` | LFM1 | Date de création LFM1 |
| `Created By LFM1` | LFM1 | Utilisateur créateur LFM1 |
| `Terms of Payment LFM1` | LFM1 | Conditions de paiement niveau matériel |
| `Terms Match` | Calculé | Résultat de la comparaison |

## Fichiers de sortie

Générés dans le dossier courant ou un dossier de run horodaté :

| Fichier | Contenu |
|---|---|
| `suppliers_payements.xlsx` | Toutes les lignes après filtres |
| `suppliers_payements_issue.xlsx` | Lignes où `Terms Match` != `True` |

## Email envoyé

| Condition | Sujet | Pièce jointe |
|---|---|---|
| Issues présentes | `Supplier Terms of Payment` | `suppliers_payements_issue.xlsx` |
| Aucune issue | `Supplier Terms of Payment` | Aucune |
