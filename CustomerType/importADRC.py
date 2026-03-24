from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv")


def _norm_addr(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.zfill(10).str[-10:]


def load_adrc(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 11:
        raise ValueError(f"ADRC malformed: expected at least 12 columns, got {df.shape[1]}")

    df = df.iloc[:, [0, 11]].copy()
    df.columns = ["Addr. No.", "BP Country"]
    df["Addr. No."] = _norm_addr(df["Addr. No."])
    df["BP Country"] = df["BP Country"].fillna("").astype(str).str.strip().str.upper()
    df.loc[df["BP Country"] == "", "BP Country"] = pd.NA
    df = df[df["Addr. No."] != ""].reset_index(drop=True)
    df = df.drop_duplicates(subset=["Addr. No."], keep="first").reset_index(drop=True)
    return df

if __name__ == "__main__":
    df = load_adrc()
    print(df.describe)