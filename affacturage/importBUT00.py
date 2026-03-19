from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def load_but00() -> pd.DataFrame:
    df = pd.read_csv(
        PATH,
        dtype=str,
        sep=";",
        on_bad_lines="warn",
    )

    df = df.iloc[:, [0, 7, 11, 12]]
    df.columns = ["BP", "Name", "Last Name", "First Name"]

    df["BP"] = df["BP"].str.strip().str.zfill(7).str[-7:]

    df = df[df["BP"] != ""].reset_index(drop=True)
    
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~personnes].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])


    # Keep one row per customer to keep joins deterministic.
    df = df.drop_duplicates(subset=["BP"], keep="first").reset_index(drop=True)
    df = df.sort_values(by=["BP"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    but00 = load_but00()
    print(but00.head())
