from pathlib import Path

import pandas as pd
from logger import log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT020.csv")


def load_but020(path: Path | str = PATH, logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = log_helpers(logger)
    log(f"Loading BUT020 from {path}")
    df = pd.read_csv(
        path,
        dtype=str,
        sep=";",
        # Source can contain malformed quoted lines.
        on_bad_lines="skip",
        engine="python",
    )
    df = df.iloc[:, :2].copy()
    df.columns = ["BP", "Addr. No."]
    df["BP"] = df["BP"].fillna("").str.strip().str.zfill(7).str[-7:]
    df["Addr. No."] = df["Addr. No."].fillna("").str.strip().str.zfill(10).str[-10:]
    df = df[(df["BP"] != "") & (df["Addr. No."] != "")].reset_index(drop=True)
    # Keep one address per BP for stable merge cardinality.
    df = df.drop_duplicates(subset=["BP"]).reset_index(drop=True)
    log(f"BUT020 loaded: {len(df)} rows")
    return df


if __name__ == "__main__":
    but020 = load_but020()
    print(but020.head())
