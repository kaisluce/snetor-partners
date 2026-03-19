# Data Dictionary (partners)

Ce fichier contient des notes historiques; les dictionnaires projet `*/DATA_DICTIONARY.md` sont maintenant la reference a jour.

## afacturage/KNB1.xlsx
- **Type**: Excel (source locale)
- **Colonnes utilisees (par position)**:
  - index `0` / Excel `A`: `Customer`
  - index `1` / Excel `B`: `Company Code`
  - index `2` / Excel `C`: `Created On`
  - index `3` / Excel `D`: `Created by`
  - index `6` / Excel `G`: `Terms of Payment`
  - index `8` / Excel `I`: `AR Pledging Ind.`
- **Nettoyage habituel**:
  - `Customer`: `def _norm_customer(series: pd.Series) -> pd.Series:
                cleaned = series.fillna("").astype(str).str.strip()
                cleaned = cleaned.str.lstrip("0")
                return cleaned.replace("", "0")`
  - filtre frequent: `Customer` commence par `1`/`2` (ou exclusion prefix `9` selon projet)
  - filtre frequent: `Company Code == FR14`

## BP__KNVV.csv (share)
- **Chemin**: `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVV.csv`
- **Type**: CSV `;`
- **Colonnes utilisees (par position)**:
  - index `0` / Excel `A`: `Customer`
  - index `1` / Excel `B`: `SalesOrg`
  - index `4` / Excel `E`: `Created By KNVV`
  - index `5` / Excel `F`: `Created On KNVV`
  - index `39` / Excel `AL`: `Sales Group KNVV` (groupe de commerciaux associe au partenaire)
- **Nettoyage habituel**:
  - `Customer`: `def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")`
  - `SalesOrg`: `str.strip().str.upper()`
- **Cle de jointure courante**:
  - `partner_id_org_com = Customer + "_" + SalesOrg`

## BP_BUT000.csv (share)
- **Chemin**: `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv`
- **Type**: CSV `;`
- **Colonnes utilisees (par position)**:
  - index `0` / Excel `A`: `BP` (ou `Customer` selon script)
  - index `5` / Excel `F`: `Search Term 1`
  - index `6` / Excel `G`: `Search Term 2`
  - index `7` / Excel `H`: `Name`
  - index `10` / Excel `K`: `Name 2`
  - index `11` / Excel `L`: `Last Name`
  - index `12` / Excel `M`: `First Name`
  - index `13` / Excel `N`: `Created On` (dans certains scripts)
  - index `14` / Excel `O`: `Created By` (dans certains scripts)
  - index `15` / Excel `P`: `Name 3`
  - index `16` / Excel `Q`: `Name 4`
- **Nettoyage habituel**:
  - `BP`: `def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")`
  - exclusion frequente: `Name` commencant par `#` (apres jointure avec la table utilisee dans le main pour filtrage par nom)
  - en Address-Language: exclusion aussi sur `Last Name` et `First Name` commencant par `#`

## BP_BUT020.csv (share)
- **Chemin**: `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT020.csv`
- **Type**: CSV `;`
- **Colonnes utilisees (par position)**:
  - index `0` / Excel `A`: `BP`
  - index `1` / Excel `B`: `Addr. No.`
- **Usage**:
  - fait le lien entre Business Partner et numero d'adresse
  - sert de pont pour joindre ADRC
- **Nettoyage habituel**:
  - `BP`: `def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")`
  - `Addr. No.`: `str.strip().str.zfill(10).str[-10:]`
  - souvent dedup sur `BP` (1 adresse principale par BP selon besoin)

## ADRC.csv (share)
- **Chemin**: `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv`
- **Type**: CSV `;` (nom exact du fichier selon export)
- **Colonnes utilisees (par position)**:
  - index `0` / Excel `A`: `Addr. No.` (cle de jointure)
  - index `26` / Excel `AA`: `street`
  - index `29` / Excel `AD`: `street4`
  - index `20` / Excel `U`: `street5`
  - index `5` / Excel `F`: `city`
  - index `4` / Excel `E`: `postcode`
  - index `11` / Excel `L`: `country`
- **Usage**:
  - enrichir un BP avec son adresse via la jointure `Addr. No.`
  - chaine de join classique: `BP` -> `BUT020` -> `ADRC`

## BP_USER_GPMSAL.csv
- **Path**: `\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_USER_GPMSAL.csv`
- **Columns used**:
  - index `0` / Excel `A`: `BP`
  - index `1` / Excel `B`: `Affected User`

## Cles/joins usuels
- **Paiements**:
  - base: KNB1
  - join KNVV sur `partner_id_org_com`
  - join BUT00 sur `Customer` (pour recuperer `Name` et filtrer `#`)
  - note: dans KNVV, la colonne `AL` correspond au `Sales Group` (pas aux conditions de paiement)
- **Afacturage**:
  - base souvent KNB1
  - enrichissement via KVV + BUT00

## Rappel Excel letters
- `A=0`, `B=1`, ... `E=4`, `F=5`, `AL=37` (index pandas 0-based)
## 2026-03 Refresh

This root file is now a lightweight index.

- The project-level `DATA_DICTIONARY.md` files are the authoritative source.
- Legacy notes below are kept for historical context and may be stale.

Project dictionaries available:
- `Address-Language/DATA_DICTIONARY.md`
- `affacturage/DATA_DICTIONARY.md`
- `bp-enrisher/DATA_DICTIONARY.md`
- `check_semicolon/DATA_DICTIONARY.md`
- `CreditVue/DATA_DICTIONARY.md`
- `CustomerType/DATA_DICTIONARY.md`
- `Family-Producer/DATA_DICTIONARY.md`
- `findDROM/DATA_DICTIONARY.md`
- `ON-Going-Check/DATA_DICTIONARY.md`
- `payements/DATA_DICTIONARY.md`
- `reformateName/DATA_DICTIONARY.md`
- `SalesUser/DATA_DICTIONARY.md`
- `Tax-Exemption/DATA_DICTIONARY.md`
- `TaxClassification/DATA_DICTIONARY.md`
