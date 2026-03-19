"""
Load BP_BUT000.csv (Business Partner core data).

Expected columns (by position in the CSV export):
- index 0 / Excel A: BP
- index 7 / Excel H: Name

Notes:
- Normalizes BP by trimming and removing leading zeros.
- Drops rows with empty BP.
- Drops names starting with "#".
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def _norm_bp(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_but000(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 7:
        raise ValueError(f"BP_BUT000.csv malformed: expected at least 8 columns, got {df.shape[1]}")

    df = df.iloc[:, [0, 7]].copy()
    df.columns = ["BP", "Name"]

    df["BP"] = _norm_bp(df["BP"])
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()

    df = df[df["BP"] != ""].reset_index(drop=True)
    df = df[~df["Name"].str.startswith("#", na=False)].reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_but000().head())
