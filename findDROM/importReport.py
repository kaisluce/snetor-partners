"""
Resolve the most recent report folder under BP-AUTOCHECKS.

Report folders follow the pattern: YYYY-MM-DD_HH-MM_REPORT.
We prefer parsing the timestamp from the folder name; if parsing fails,
we fall back to the folder's last modification time.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

REPORTS_ROOT = Path(r"Z:\MDM\998_CHecks\BP-AUTOCHECKS")

RELATIVE_REPORT_PATH = r"siren_siret\latest_report.xlsx"


def _parse_report_ts(folder_name: str) -> Optional[datetime]:
    try:
        # Expected format: YYYY-MM-DD_HH-MM_REPORT
        return datetime.strptime(folder_name, "%Y-%m-%d_%H-%M_REPORT")
    except ValueError:
        return None


def _norm_bp(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")


def get_latest_report_dir(root: Path = REPORTS_ROOT) -> Path:
    """
    Return the path of the most recent report folder.

    Only directories ending with "_REPORT" are considered.
    """
    if not root.exists():
        raise FileNotFoundError(f"Reports root not found: {root}")

    candidates: list[Tuple[datetime, Path]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if not entry.name.endswith("_REPORT") and not "HANDCHECK" in entry.name:
            continue
        ts = _parse_report_ts(entry.name)
        if ts is None:
            # Fallback: use mtime if name is unexpected.
            ts = datetime.fromtimestamp(entry.stat().st_mtime)
        candidates.append((ts, entry))

    if not candidates:
        raise FileNotFoundError(f"No report folders found in: {root}")

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def load_report_xlsx(
    relative_path: str | Path = RELATIVE_REPORT_PATH, root: Path = REPORTS_ROOT
) -> pd.DataFrame:
    """
    Load an Excel file from the most recent report folder.

    Parameters
    - relative_path: path relative to the latest report folder.
      Example: "reports/checks.xlsx" or "summary.xlsx".
    """
    report_dir = get_latest_report_dir(root)
    file_path = report_dir / Path(relative_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Report file not found: {file_path}")
    df = pd.read_excel(file_path, dtype=str)
    if "BP" in df.columns:
        df["BP"] = _norm_bp(df["BP"])
    return df



if __name__ == "__main__":
    print(load_report_xlsx())
    
