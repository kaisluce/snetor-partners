"""
Load BP_BUT020.csv (BP to Address Number link).

Expected columns (by position in the CSV export):
- index 0 / Excel A: BP
- index 1 / Excel B: Addr. No.
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT020.csv")


def _norm_bp(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def _norm_addr(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.zfill(10).str[-10:]


def load_but020(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 1:
        raise ValueError(f"BP_BUT020.csv malformed: expected at least 2 columns, got {df.shape[1]}")

    df = df.iloc[:, [0, 1]].copy()
    df.columns = ["BP", "Addr. No."]

    df["BP"] = _norm_bp(df["BP"])
    df["Addr. No."] = _norm_addr(df["Addr. No."])

    df = df[(df["BP"] != "") & (df["Addr. No."] != "")].reset_index(drop=True)

    # Keep one address per BP (highest address number as a stable default).
    idx = df.groupby("BP")["Addr. No."].idxmax()
    return df.loc[idx, ["BP", "Addr. No."]].reset_index(drop=True)


if __name__ == "__main__":
    print(load_but020().head())
