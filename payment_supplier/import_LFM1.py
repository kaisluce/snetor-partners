from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__LFM1.csv")

COLS = {
    0 : "Supplier",
    1 : "Company Code",
    2 : "Created On LFM1",
    3 : "Created By LFM1",
    7 : "Terms of Payment LFM1",
}

def load_lfm1() -> pd.DataFrame:
    df = pd.read_csv(PATH, sep=";", dtype=str,)
    df = df.iloc[:, [key for key in COLS.keys()]]
    df.columns = COLS.values()
    df = df[df["Supplier"] != ""].reset_index(drop=True)
    df = df.sort_values(by=["Supplier", "Company Code", "Terms of Payment LFM1"]).reset_index(drop=True)
    df.drop_duplicates(subset=["Supplier", "Company Code"], keep="first", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == "__main__":
    print(load_lfm1().head())