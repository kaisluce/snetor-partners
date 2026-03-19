from pathlib import Path

import pandas as pd

PATH = Path(r"C:\Users\K.luce\OneDrive - SNETOR\Documents\partners\TaxClassification\EXPORT_20260129_140600.xlsx")


def load_countries(path: Path = PATH, sheet_name: int | str = 0) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name, dtype=str)
    df = df.iloc[:, :3].copy()
    df.columns = ["SalesOrg", "Plant", "Country"]
    df = df.reset_index(drop=True)
    df = df[df["SalesOrg"] != "FR13"].reset_index(drop=True)
    df.drop_duplicates(subset=["SalesOrg", "Country"], inplace=True)
    return df


if __name__ == "__main__":
    countries = load_countries()
    print(countries.head())
