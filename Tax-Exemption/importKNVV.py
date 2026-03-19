from pathlib import Path

import pandas as pd
from logger import _log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVV.csv")


def load_knvv(path: Path = PATH, logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = _log_helpers(logger)
    log(f"Loading KNVV from {path}")
    df = pd.read_csv(
        path, 
        dtype=str,
        sep=';',
        on_bad_lines='warn'
        )
    df = df.iloc[:, :2].copy()
    df.columns = ["BP", "SalesOrg"]
    df["BP"] = df["BP"].str.zfill(7)
    df["BP"] = df["BP"].str[-7:]
    df = df.drop_duplicates(subset=["BP", "SalesOrg"]).reset_index(drop=True)
    df = df.sort_values(by=["BP", "SalesOrg"]).reset_index(drop=True)
    df = df[df["SalesOrg"] != "FR13"].reset_index(drop=True)
    df = df[df["BP"].str.startswith("9") == False].reset_index(drop=True)
    df = df[df["BP"].str.isdigit() == True].reset_index(drop=True)
    log(f"KNVV loaded: {len(df)} rows")
    return df


if __name__ == "__main__":
    knvv = load_knvv()
    print(knvv.head())
