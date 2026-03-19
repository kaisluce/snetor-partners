"""
Charge l'export "credit vue" utilise pour comparer les limites de credit.

Le fichier Excel doit contenir au minimum les colonnes A, B et E :
- A : Customer
- B : Company Code
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_UKM.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    """Normalise la cle client : trim, supprime les zeros a gauche, remplace vide par "0"."""
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_ukm(path: Path = PATH) -> pd.DataFrame:
    """
    Charge et nettoie l'export Excel.

    Parametres
    - path : chemin vers le csv.

    Retour
    - DataFrame avec `Customer`, `Company Code`, `Limit Valid To`.
    """
    # Colonnes A, B
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="warn")
    if df.shape[1] < 3:
        raise ValueError(f"EXPORT malformed: expected 3 columns (A,B,E), got {df.shape[1]}")
    
    df = df.iloc[:, :2]  # En cas de colonnes supplémentaires, ne garder que les 2 premières

    df.columns = ["Customer", "Company Code"]
    df["Customer"] = _norm_customer(df["Customer"])
    df["Company Code"] = df["Company Code"].fillna("").astype(str).str.strip().str.upper()
    df = df[~df["Company Code"].str.contains("FR13|FR10|0")].reset_index(drop=True)

    df = df[df["Customer"] != ""].reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_ukm().head())
