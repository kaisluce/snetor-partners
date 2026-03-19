from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVV.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_knvv(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="warn")
    if df.shape[1] <= 37:
        raise ValueError(f"KNVV malformed: expected at least 38 columns, got {df.shape[1]}")

    # A=Customer, B=SalesOrg, E/F=creator/creation date, AL(index 37)=Sales Group
    df = df.iloc[:, [0, 1, 4, 5, 39]].copy()
    df.columns = [
        "BP",
        "SalesOrg",
        "Created By (KNVV)",
        "Created On (KNVV)",
        "Sales Group",
    ]

    df["BP"] = _norm_customer(df["BP"])
    df["SalesOrg"] = df["SalesOrg"].fillna("").astype(str).str.strip().str.upper()
    df["Created By (KNVV)"] = df["Created By (KNVV)"].fillna("").astype(str).str.strip().str.upper()
    df["Created On (KNVV)"] = df["Created On (KNVV)"].fillna("").astype(str).str.strip()
    df["Sales Group"] = df["Sales Group"].fillna("").astype(str).str.strip().str.upper()

    df = df[(df["BP"] != "") & (df["SalesOrg"] != "")].reset_index(drop=True)
    df = df.drop_duplicates(subset=["BP", "SalesOrg"], keep="first").reset_index(drop=True)
    df["BP"] = df["BP"].str.strip().str.lstrip("0")
    return df


if __name__ == "__main__":
    knvv = load_knvv()
    print(f"Loaded {len(knvv)} rows and {len(knvv.columns)} columns from {PATH}")
    print(knvv.head())
