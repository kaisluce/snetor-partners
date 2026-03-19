"""Merge BUT000, BUT020, and ADRC exports for semicolon and double-quote checks."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from importADRC import load_adrc
from importBUT000 import load_but000
from importBUT020 import load_but020_main_addr

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"


def build_merged_df():
    but000 = load_but000()
    but020 = load_but020_main_addr()
    adrc = load_adrc()

    addr = but020.merge(adrc, on="Addr. No.", how="left")
    addr = addr.rename(columns={"Addr. No.": "Addr. No. BUT020"})

    but000 = but000.rename(columns={"Addr. No.": "Addr. No. BUT000"})

    df = but000.merge(addr, on="BP", how="left")
    return df


def filter_rows_with_special_chars(df):
    if df.empty:
        return df
    text = df.fillna("").astype(str)
    has_semi = text.apply(lambda col: col.str.contains(";", regex=False))
    has_quote = text.apply(lambda col: col.str.contains('"', regex=False))
    has_special = has_semi | has_quote
    mask = has_special.any(axis=1)

    filtered = df[mask].copy()
    where_vals = has_special[mask].apply(
        lambda row: ",".join([col for col, hit in row.items() if hit]),
        axis=1,
    )
    filtered["where"] = where_vals
    return filtered.reset_index(drop=True)


def main() -> None:
    df = build_merged_df()
    issues = filter_rows_with_special_chars(df)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"special_char_issues_{ts}.xlsx"
    issues.to_excel(out_path, index=False)
    print(f"[INFO] merged rows={len(df)} cols={len(df.columns)}")
    print(f"[INFO] rows with ';' or '\"'={len(issues)}")
    print(f"[INFO] saved: {out_path}")
    print(issues.head())


if __name__ == "__main__":
    main()

