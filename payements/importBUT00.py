from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def load_but00() -> pd.DataFrame:
    df = pd.read_csv(
        PATH,
        dtype=str,
        sep=";",
        on_bad_lines="skip",
    )

    df = df.iloc[:, [0, 7, 11, 12]]
    df.columns = ["Customer", "Name", "Last Name", "First Name"]

    df["Customer"] = df["Customer"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["Name"] = df["Name"].fillna("").str.strip()
    
    
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~personnes].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])

    df = df[df["Customer"] != ""].reset_index(drop=True)
    return df
