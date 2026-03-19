from pathlib import Path

import pandas as pd
from logger import _log_helpers

PATH = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")

# Fallback indexes in BP_BUT000.csv when headers are missing.
BP_INDEX = 0
GROUP_INDEX = 1
NAME1_INDEX = 7
NAME2_INDEX = 8
NAME3_INDEX = 9
NAME4_INDEX = 10
LAST_NAME_INDEX = 11
FIRST_NAME_INDEX = 12
CREATION_DATE_INDEX = 13
DECREATOR_INDEX = 14


def _pick_column(df: pd.DataFrame, name: str, index: int) -> pd.Series:
    """Prefer a named column when present, otherwise use positional index."""
    if name in df.columns:
        return df[name]
    if df.shape[1] <= index:
        raise ValueError(f"BUT000 malformed: expected at least {index + 1} columns, got {df.shape[1]}")
    return df.iloc[:, index]


def load_but00(path: Path = PATH, logger=None) -> pd.DataFrame:
    _debug, _log, _warn, _error = _log_helpers(logger)
    try:
        df = pd.read_csv(path, dtype=str, sep=";", on_bad_lines="warn")

        out = pd.DataFrame(
            {
                "Bp": _pick_column(df, "BP", BP_INDEX),
                "Group": _pick_column(df, "GROUP", GROUP_INDEX),
                "Name 1": _pick_column(df, "Name 1", NAME1_INDEX),
                "Name 2": _pick_column(df, "Name 2", NAME2_INDEX),
                "Name 3": _pick_column(df, "Name 3", NAME3_INDEX),
                "Name 4": _pick_column(df, "Name 4", NAME4_INDEX),
                "Last Name": _pick_column(df, "LAST NAME", LAST_NAME_INDEX),
                "First Name": _pick_column(df, "FIRST NAME", FIRST_NAME_INDEX),
                "Decreator": _pick_column(df, "DECREATOR", DECREATOR_INDEX),
                "Creation date": _pick_column(df, "CREATION DATE", CREATION_DATE_INDEX),
            }
        )

        for col in ["Name 1", "Name 2", "Name 3", "Name 4", "Decreator", "Creation date", "Group", "Last Name", "First Name"]:
            out[col] = out[col].fillna("").astype(str).str.strip()

        out = out[out["Bp"] != ""].drop_duplicates(subset=["Bp"], keep="first").reset_index(drop=True)

        combined_name = (
            out[["Name 1", "Name 2", "Name 3", "Name 4"]]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        personnes = (combined_name == "") & ~((out["Last Name"] == "") & (out["First Name"] == ""))
        out = out[~personnes].reset_index(drop=True)
        out = out.drop(columns=["Last Name", "First Name"])
        _log(f"[BUT000] Loaded {len(out)} rows from {path}")
        return out
    except Exception as exc:
        _error(f"[BUT000] Failed to load data from {path}: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    from logger import logger as app_logger

    log = app_logger()
    _debug, _log, _warn, _error = _log_helpers(log)
    df = load_but00(logger=log)
    _log(f"[BUT000] Sample:\n{df.head().to_string(index=False)}")
