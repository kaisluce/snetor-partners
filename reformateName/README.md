# reformateName

Outil interactif de reformatage des colonnes de nom pour les adapter aux contraintes SAP (35 caractères max par champ, répartition sur Name 1 / Name 2 / Name 3).

## Objectif

Quand un nom de BP dépasse la limite de 35 caractères d'un champ SAP, cet outil découpe automatiquement le nom en plusieurs colonnes (`Name 1`, `Name 2`, `Name 3`) en respectant les coupures de mots.

## Exécution

```
python main.py
```

L'outil fonctionne en mode interactif via la ligne de commande :

1. Demande le chemin du fichier XLSX source.
2. Affiche les colonnes disponibles et demande de sélectionner la colonne nom à reformater.
3. Demande la longueur maximale par champ (défaut : 35 caractères).
4. Génère le fichier de sortie.

## Fichier d'entrée

Fichier XLSX fourni par l'utilisateur contenant au moins une colonne de nom à reformater. Aucun chemin fixe : le chemin est saisi interactivement.

## Logique de reformatage

1. Pour chaque valeur de la colonne nom :
   - Si la valeur fait <= 35 caractères : placée dans `Name 1`, `Name 2` et `Name 3` vides.
   - Si la valeur dépasse 35 caractères : découpage mot par mot.
     - Les mots sont ajoutés à `Name 1` tant que la longueur ne dépasse pas 35.
     - Le reste est traité de la même façon pour `Name 2`, puis `Name 3`.
2. Validation : une erreur est signalée si `Name 3` dépasse encore 35 caractères après découpage.

## Colonnes de sortie

Le fichier d'entrée est enrichi des colonnes :

| Colonne | Description |
|---|---|
| `Name 1` | Première partie du nom (max 35 car.) |
| `Name 2` | Deuxième partie du nom (max 35 car., si nécessaire) |
| `Name 3` | Troisième partie du nom (max 35 car., si nécessaire) |

## Fichier de sortie

| Fichier | Contenu |
|---|---|
| `<nom_fichier_source>_update.xlsx` | Fichier source avec les colonnes Name 1/2/3 ajoutées |
