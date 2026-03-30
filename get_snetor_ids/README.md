# get_snetor_ids

Extraction de tous les Business Partners identifiés comme entités internes SNETOR depuis BUT000.

## Objectif

Produire une liste exhaustive des BP dont le nom correspond à une entité du groupe SNETOR, pour alimenter les listes d'exclusion des autres scripts de contrôle.

## Exécution

```
python main.py
```

## Fichiers d'entrée

| Fichier | Colonnes extraites |
|---|---|
| `BP_BUT000.csv` | A=BP, H=Name |

Chemin réseau : `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\`

## Logique de filtrage

Le script charge BUT000 et filtre les lignes dont le `Name` contient (insensible à la casse) l'une des 47 chaînes SNETOR définies en dur :

`SNETOR`, `SNETOR OVERSEAS`, `SNETOR MAROC`, `EIXO SNETOR BRASIL`, `SNETOR ECUADOR`, `SNETOR FRANCE`, `OZYANCE`, `SNETOR KOREA`, `SNETOR EGYPT`, `SNETOR SOUTH AFRICA`, `SNETOR COLOMBIA`, `SNETOR CHILE`, `SNETOR UK LTD`, `TECNOPOL SNETOR ITALIA`, `SNETOR SHANGHAI`, `SNETOR WEST AFRICA LTD`, `SNETOR EAST AFRICA`, `SNETOR PERU`, `SNETOR USA`, `SNETOR BENELUX`, `OZYANCE ITALIA`, `SNETOR DISTRIBUTION UGANDA`, `SNETOR MIDDLE EAST`, `COANSA SNETOR COSTA RICA`, `COANSA SNETOR EL SALVADOR`, `SNETOR NORDEN`, `LEONARDI`, `SNETOR MUSQAT`, `COANSA SNETOR GUATEMALA`, `SNETOR MEXICO`, `SNETOR GERMANY GMBH`, `TECNOPOL SNETOR IBERIA`, `SNETOR EASTERN EUROPE`, `SNETOR BALKAN`, `MEG SNETOR TURKIYE`, `SNETOR LOGISTICS`, et variantes.

Le résultat est trié par `Name`.

## Colonnes de sortie

| Colonne | Description |
|---|---|
| `BP` | Identifiant Business Partner |
| `Name` | Dénomination de l'entité SNETOR |

## Fichier de sortie

| Fichier | Contenu |
|---|---|
| `snetor_ids.xlsx` | Liste des BP SNETOR triés par Name |
