from pathlib import Path

import pandas as pd
from logger import log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP__KNVI.csv")


def load_knvi(path: Path = PATH, logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = log_helpers(logger)
    log(f"Loading KNVI from {path}")
    df = pd.read_csv(
        path, 
        dtype=str,
        sep=';',
        on_bad_lines='warn'
        )
    df = df.iloc[:, :4].copy()
    df.columns = ["ID", "country", "Cond type", "Tax indicator"]
    df["ID"] = df["ID"].str.zfill(7)
    df["ID"] = df["ID"].str[-7:]
    df = df.reset_index(drop=True)
    df["Key"] = df["ID"] + df["country"]
    df = df.sort_values(by=["ID", "country"]).reset_index(drop=True)
    df = df[df["ID"].str.startswith("9") == False].reset_index(drop=True)
    log(f"KNVI loaded: {len(df)} rows")
    return df


if __name__ == "__main__":
    knvi = load_knvi()
    print(knvi.tail(1500).head(20))
