"""
Charge le fichier KNB1 (donnees credit / societe) utilise pour comparaison.

Fichier attendu : Excel avec au moins les colonnes suivantes :
- Customer
- Created by
- Created On
- Company Code (utilise ici comme SalesOrg)
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNB1.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    """Normalise la cle client : trim, supprime les zeros a gauche, remplace vide par "0"."""
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_knb1(path: Path = PATH) -> pd.DataFrame:
    """
    Charge et nettoie le fichier KNB1.

    Retour
    - DataFrame avec `Customer`, `Company Code`, `Created By KNB1`, `Created On KNB1`.
    """
    df = pd.read_csv(path, dtype=str, sep=";", engine="python", on_bad_lines="warn")
    df = df.iloc[:, [0, 4, 3, 1]]  # En cas de colonnes supplémentaires, ne garder que les 4 premières
    df.columns = ["Customer", "Created By KNB1", "Created On KNB1", "Company Code"]

    df["Customer"] = _norm_customer(df["Customer"])
    df["Company Code"] = df["Company Code"].fillna("").astype(str).str.strip().str.upper()
    df["Created By KNB1"] = df["Created By KNB1"].fillna("").astype(str).str.strip().str.upper()
    df["Created On KNB1"] = df["Created On KNB1"].fillna("").astype(str).str.strip()
    df = df[~df["Company Code"].str.contains("FR13|FR10", na=False)].reset_index(drop=True)  # Seules les lignes FR13 et FR10 sont pertinentes pour la comparaison

    df = df[(df["Customer"] != "") & (df["Company Code"] != "")].reset_index(drop=True)
    print(f"Unique customers in KNB1: {df['Customer'].nunique()}")
    return df


if __name__ == "__main__":
    knb1 = load_knb1()
    print(knb1.head())
    print(knb1[knb1["Customer"] == "1000002"])

#virer fr13 fr10