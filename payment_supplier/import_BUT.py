"""
Load BP_BUT000.csv (Business Partner core data) for supplier context.

Expected columns (by position in the CSV export):
- index 0  / Excel A : BP (Supplier)
- index 7  / Excel H : Name
- index 11 / Excel L : Last Name
- index 12 / Excel M : First Name

Notes:
- Normalizes Supplier to 7-digit zero-padded string (matches LFB1 / LFM1 keys).
- Drops individuals (empty Name but non-empty Last/First Name).
- Drops rows with empty Supplier.
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def load_but() -> pd.DataFrame:
    df = pd.read_csv(PATH, dtype=str, sep=";", on_bad_lines="skip")

    if df.shape[1] <= 12:
        raise ValueError(f"BP_BUT000.csv malformed: expected at least 13 columns, got {df.shape[1]}")

    df = df.iloc[:, [0, 7, 11, 12]].copy()
    df.columns = ["Supplier", "Name", "Last Name", "First Name"]

    df["Supplier"] = df["Supplier"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["Name"] = df["Name"].fillna("").str.strip()
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()

    # Drop individuals: no company name but has a personal name
    individuals = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~individuals].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])

    df = df[df["Supplier"] != ""].reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_but().head())
