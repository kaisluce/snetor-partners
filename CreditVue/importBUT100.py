"""
Charge le fichier BUT100 (roles du Business Partner).

Le CSV provient de l'export MDM (reseau) et contient au moins :
- Colonne 1 : Customer (BP)
- Colonne 2 : Role (ex. FLCU01, UKM000)
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__BUT100.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    """Normalise la cle client : trim, supprime les zeros a gauche, remplace vide par "0"."""
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_but100(path: Path = PATH) -> pd.DataFrame:
    """
    Charge et nettoie le fichier BUT100.

    Retour
    - DataFrame avec `Customer` et `Role` (deduplique).
    """
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="warn")
    if df.shape[1] <= 1:
        raise ValueError(f"BUT100 malformed: expected at least 2 columns, got {df.shape[1]}")

    df = df.iloc[:, :2].copy()
    df.columns = ["Customer", "Role"]

    df["Customer"] = _norm_customer(df["Customer"])
    df["Role"] = df["Role"].fillna("").astype(str).str.strip().str.upper()

    df = df[(df["Customer"] != "") & (df["Role"] != "")].reset_index(drop=True)
    df = df.drop_duplicates(subset=["Customer", "Role"], keep="first").reset_index(drop=True)
    return df


def getbut100() -> pd.DataFrame:
    """Alias historique de load_but100() pour compatibilite."""
    return load_but100()


if __name__ == "__main__":
    print(load_but100().head())
