from pathlib import Path

import pandas as pd

PATH = Path(__file__).resolve().parent / "LFM1.xlsx"

COLS = {
    0 : "Supplier",
    1 : "Company Code",
    2 : "Created On LFM1",
    3 : "Created By LFM1",
    7 : "Terms of Payment",
}

def load_lfm1() -> pd.DataFrame:
    df = pd.read_excel(PATH, dtype=str,)
    df = df.iloc[:, [key for key in COLS.keys()]]
    df.columns = COLS.values()
    df = df[df["Supplier"] != ""].reset_index(drop=True)
    df = df[df["Company Code"] != ""].reset_index(drop=True)
    df.drop_duplicates(subset=["Supplier", "Company Code"], keep="first", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


if __name__ == "__main__":
    print(load_lfm1().head())