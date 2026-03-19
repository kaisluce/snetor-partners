from pathlib import Path

import pandas as pd
from logger import _log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv")


def load_adrc(path: Path | str = PATH, logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = _log_helpers(logger)
    log(f"Loading ADRC from {path}")
    df = pd.read_csv(
        path,
        dtype=str,
        sep=";",
        # Source can contain malformed quoted lines.
        on_bad_lines="skip",
        engine="python",
    )
    # Keep only Addr. No. (col 0) and BP Country (col L => index 11).
    df = df.iloc[:, [0, 11]].copy()
    df.columns = ["Addr. No.", "BP Country"]
    df["Addr. No."] = df["Addr. No."].fillna("").str.strip().str.zfill(10).str[-10:]
    df["BP Country"] = df["BP Country"].fillna("").str.strip()
    df = df.drop_duplicates(subset=["Addr. No."]).reset_index(drop=True)
    log(f"ADRC loaded: {len(df)} rows")
    return df


if __name__ == "__main__":
    adrc = load_adrc()
    print(adrc.head())
