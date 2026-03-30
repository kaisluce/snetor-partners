from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNB1.csv")


def load_knb1() -> pd.DataFrame:
    df = pd.read_csv(PATH, dtype=str, sep=";")
    df = df.iloc[:, [0, 1, 3, 4, 7]]
    df.columns = ["Customer", "Company Code", "Created On", "Created by", "AR Pledging Ind."]

    df["Customer"] = df["Customer"].str.strip().str.zfill(7).str[-7:]
    df["Company Code"] = df["Company Code"].str.strip().str.upper()
    df["AR Pledging Ind."] = df["AR Pledging Ind."].str.strip().str.upper()

    df = df[(df["Customer"] != "") & (df["Company Code"] != "")].reset_index(drop=True)
    df = df[df["Company Code"] == "FR14"].reset_index(drop=True)
    df = df[~df["Customer"].str.match(r"^0*9", na=False)].reset_index(drop=True)

    # Keep one customer line when duplicates exist.
    df = df.drop_duplicates(subset=["Customer"], keep="first").reset_index(drop=True)
    df = df.sort_values(by=["Customer"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    knb1 = load_knb1()
    print(knb1.head())
