from pathlib import Path

import pandas as pd
from logger import _log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")


def load_but(path: Path = PATH, logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = _log_helpers(logger)
    log(f"Loading BUT000 from {path}")
    df = pd.read_csv(
        path,
        dtype=str,
        sep=";",
        on_bad_lines="warn",
    )
    df = df.iloc[:, [0, 7, 11, 12, 13, 14]].copy()
    df.columns = ["BP", "Name", "Last Name", "First Name", "Creation date", "Created by"]
    df["BP"] = df["BP"].str.strip().str.lstrip("0")
    
    
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    df = df[~personnes].reset_index(drop=True)
    df = df.drop(columns=["Last Name", "First Name"])
    log(f"BUT000 loaded: {len(df)} rows")
    return df


if __name__ == "__main__":
    but = load_but()
    print(but.head())
