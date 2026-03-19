from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_but00(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="skip", engine="python")
    if df.shape[1] <= 7:
        raise ValueError(f"BUT000 malformed: expected at least 8 columns, got {df.shape[1]}")

    # A=Customer(BP), H=Name
    df = df.iloc[:, [0, 7, 11, 12]].copy()
    df.columns = ["BP", "Name", "Last Name", "First Name"]

    df["BP"] = _norm_customer(df["BP"])
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()

    df = df[df["BP"] != ""].reset_index(drop=True)
    df = df.drop_duplicates(subset=["BP"], keep="first").reset_index(drop=True)
    df["BP"] = df["BP"].str.strip().str.lstrip("0")
    
    
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~personnes].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])
    return df


if __name__ == "__main__":
    but00 = load_but00()
    print(f"Loaded {len(but00)} rows and {len(but00.columns)} columns from {PATH}")
    print(but00.head())
