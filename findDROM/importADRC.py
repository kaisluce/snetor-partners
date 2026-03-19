"""
Load BP_ADRC.csv (address master).

Expected columns (by position in the CSV export):
- index 0 / Excel A: Addr. No. (join key)
- index 26 / Excel AA: street
- index 29 / Excel AD: street4
- index 20 / Excel U: street5
- index 5 / Excel F: city
- index 4 / Excel E: postcode
- index 11 / Excel L: country
"""

from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv")


def _norm_addr(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.zfill(10).str[-10:]


def load_adrc(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 0:
        raise ValueError(f"BP_ADRC.csv malformed: expected at least 1 column, got {df.shape[1]}")

    rename_map: dict[str, str] = {}
    if len(df.columns) > 0:
        rename_map[df.columns[0]] = "Addr. No."
    if len(df.columns) > 26:
        rename_map[df.columns[26]] = "street"
    if len(df.columns) > 29:
        rename_map[df.columns[29]] = "street4"
    if len(df.columns) > 20:
        rename_map[df.columns[20]] = "street5"
    if len(df.columns) > 5:
        rename_map[df.columns[5]] = "city"
    if len(df.columns) > 4:
        rename_map[df.columns[4]] = "postcode"
    if len(df.columns) > 11:
        rename_map[df.columns[11]] = "country"

    df = df.rename(columns=rename_map)

    expected_cols = ["Addr. No.", "street", "street4", "street5", "city", "postcode", "country"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    df = df[expected_cols].copy()

    df["Addr. No."] = _norm_addr(df["Addr. No."])
    for col in ["street", "street4", "street5", "city", "postcode", "country"]:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df = df[df["Addr. No."] != ""].reset_index(drop=True)
    df = df.drop_duplicates(subset=["Addr. No."], keep="first").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_adrc().head())
