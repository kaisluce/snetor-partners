from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
PATH = BASE_DIR / "EXPORT_ADRC.xlsx"

ADDR_INDEX = 0


def _norm_addr(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.zfill(10).str[-10:]


def load_adrc(
    path: Path | str = PATH,
    keep_columns: list[str] | None = None,
    add_standard_cols: bool = True,
) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=str)
    raw_df = df

    if keep_columns is not None:
        missing = [c for c in keep_columns if c not in df.columns]
        if missing:
            raise ValueError(
                "EXPORT_ADRC.xlsx: missing columns: " + ", ".join(missing)
            )
        df = df[keep_columns].copy()
    else:
        df = df.copy()

    df = df.fillna("")

    if add_standard_cols:
        if raw_df.shape[1] <= ADDR_INDEX:
            raise ValueError(
                f"EXPORT_ADRC.xlsx malformed: expected at least {ADDR_INDEX + 1} columns, got {raw_df.shape[1]}"
            )
        df["Addr. No."] = _norm_addr(raw_df.iloc[:, ADDR_INDEX])

    return df


if __name__ == "__main__":
    print(load_adrc().head())
