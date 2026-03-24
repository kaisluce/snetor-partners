from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_LFB1.csv")


def load_lfb1() -> pd.DataFrame:
    df = pd.read_csv(PATH, dtype=str, sep=";", on_bad_lines="warn")
    df = df.iloc[:, [0, 1, 4, 8, 9]]
    df.columns = ["Supplier", "Company Code", "Terms of Payment LFB1", "Created On LFB1", "Created By LFB1"]

    df["Supplier"] = df["Supplier"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["Company Code"] = df["Company Code"].fillna("Missing")
    df["Created On LFB1"] = df["Created On LFB1"].fillna("")
    df["Created By LFB1"] = df["Created By LFB1"].fillna("")

    df = df[(df["Supplier"] != "") & (df["Company Code"] != "")].reset_index(drop=True)
    df = df.sort_values(by=["Supplier", "Company Code", "Terms of Payment LFB1"]).reset_index(drop=True)
    df = df.drop_duplicates(subset=["Supplier", "Company Code"], keep="first").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_lfb1().head())
