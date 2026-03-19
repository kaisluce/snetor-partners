from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVV.csv")


def _norm_customer(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def load_knvv(path: Path = PATH) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="warn")
    if df.shape[1] <= 36:
        raise ValueError(f"KNVV malformed: expected at least 37 columns, got {df.shape[1]}")

    # A=Customer, B=SalesOrg, E/F=creator/creation date, AK(index 36)=Account Assgn. Grp.
    df = df.iloc[:, [0, 1, 2, 3, 4, 5, 36]].copy()
    df.columns = [
        "Customer",
        "SalesOrg",
        "DistributionChannel",
        "Division",
        "Created By KNVV",
        "Creation Date KNVV",
        "Account Assgn. Grp. Current",
    ]

    df["Customer"] = _norm_customer(df["Customer"])
    df["SalesOrg"] = df["SalesOrg"].fillna("").astype(str).str.strip().str.upper()
    df["Created By KNVV"] = df["Created By KNVV"].fillna("").astype(str).str.strip().str.upper()
    df["Creation Date KNVV"] = df["Creation Date KNVV"].fillna("").astype(str).str.strip()
    df["Account Assgn. Grp. Current"] = (
        df["Account Assgn. Grp. Current"].fillna("").astype(str).str.strip().str.upper()
    )
    df = df[(df["Customer"] != "") & (df["SalesOrg"] != "")].reset_index(drop=True)
    df = df[~df["Customer"].str.startswith("29", na=False)].reset_index(drop=True)
    df = df[~df["Customer"].str.startswith("9", na=False)].reset_index(drop=True)

    dup_count = int(df.duplicated(subset=["Customer", "SalesOrg", "DistributionChannel", "Division"]).sum())
    if dup_count:
        print(f"[WARN] KNVV duplicate keys (Customer,SalesOrg,DistributionChannel,Division): {dup_count} -> keep first")
        df = df.drop_duplicates(subset=["Customer", "SalesOrg", "DistributionChannel", "Division"], keep="first").reset_index(drop=True)

    is_numeric = df["Account Assgn. Grp. Current"].str.fullmatch(r"\d+")
    df.loc[is_numeric, "Account Assgn. Grp. Current"] = (
        df.loc[is_numeric, "Account Assgn. Grp. Current"].str.lstrip("0").replace("", "0")
    )
    return df
