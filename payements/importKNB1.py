from pathlib import Path

import pandas as pd

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNB1.csv")


def load_knb1() -> pd.DataFrame:
    df = pd.read_csv(PATH, dtype=str, sep=";", on_bad_lines="warn")
    df = df.iloc[:, [0, 1, 3, 4, 10]]
    df.columns = ["Customer", "Company Code", "Created On", "Created by", "Terms of Payment"]
    df = df.rename(
        columns={
            "Created by": "Created By KNB1",
            "Created On": "Created On KNB1",
        }
    )

    df["Customer"] = df["Customer"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["Company Code"] = df["Company Code"].fillna("Missing")
    df["Terms of Payment"] = df["Terms of Payment"].fillna("Missing")

    df = df[(df["Customer"] != "") & (df["Company Code"] != "")]
    df = df[df["Terms of Payment"] != ""].reset_index(drop=True)

    # Keep only partners starting with 1 or 2, and exclude technical '#' IDs.
    df = df[df["Customer"].str.match(r"^0*[12]", na=False)].reset_index(drop=True)
    df = df[~df["Customer"].str.startswith("29")].reset_index(drop=True)
    df = df.drop_duplicates(subset=["Customer", "Company Code"], keep="first").reset_index(drop=True)
    return df


if __name__ == "__main__":
    print(load_knb1().head())
