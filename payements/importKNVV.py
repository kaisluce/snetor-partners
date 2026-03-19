from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVV.csv")


def load_knvv() -> pd.DataFrame:
    df = pd.read_csv(PATH, dtype=str, sep=";", on_bad_lines="warn")
    df = df.iloc[:, [0, 1, 4, 5, 37]]
    df.columns = ["Customer", "SalesOrg", "Created By KNVV", "Created On KNVV", "Terms of Payment KNVV"]

    df["Customer"] = df["Customer"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["SalesOrg"] = df["SalesOrg"].fillna("")
    df["Created By KNVV"] = df["Created By KNVV"].fillna("")
    df["Created On KNVV"] = df["Created On KNVV"].fillna("")
    df["Terms of Payment KNVV"] = df["Terms of Payment KNVV"].fillna("Missing")
    df = df[(df["Customer"] != "") & (df["SalesOrg"] != "")].reset_index(drop=True)

    df["partner_id_org_com"] = df["Customer"] + "_" + df["SalesOrg"]
    df = df.drop_duplicates(subset=["partner_id_org_com"], keep="first").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_knvv().head())
