"""
Charge le fichier BUT000 (informations de base du Business Partner).

Le CSV provient de l'export MDM (reseau) et doit contenir au minimum :
- Colonne 1 : Customer (BP)
- Colonne 8 : Name
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    """Normalise la cle client : trim, supprime les zeros a gauche, remplace vide par "0"."""
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_but00(path: Path = PATH) -> pd.DataFrame:
    """
    Charge et nettoie le fichier BUT000.

    Retour
    - DataFrame avec `Customer` et `Name`.
    """
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 7:
        raise ValueError(f"BUT000 malformed: expected at least 8 columns, got {df.shape[1]}")

    # A=Customer, H=Name
    df = df.iloc[:, [0, 7, 11, 12]].copy()
    df.columns = ["Customer", "Name", "Last Name", "First Name"]

    df["Customer"] = _norm_customer(df["Customer"])
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    
    
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~personnes].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])

    df = df[df["Customer"] != ""].reset_index(drop=True)
    return df


if __name__ == "__main__":
    but = load_but00()
    but = but[but["Name"].str.contains("#", na=False)]
    print(but.head())
