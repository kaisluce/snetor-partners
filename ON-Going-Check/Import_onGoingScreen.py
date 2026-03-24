from pathlib import Path
from datetime import datetime

import pandas as pd
from logger import log_helpers

PATH = Path(r"\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\On Going Screening\On Going Screening.csv")
CHECKS_ROOT = Path(r"\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\BP-ON_GOING_SCREEN")

ONGOING_COLUMNS = [
    "Case id",
    "Case name",
    "Entity type",
    "Group",
    "Case rating",
    "Case gender",
    "Case date of birth",
    "Case country location",
    "Case place of birth",
    "Case citizenship",
    "Case registered country",
    "Case identification number(s)",
    "Case imo number",
    "Mandatory actions",
    "World-check total matches",
    "Sanctions unresolved",
    "Re unresolved",
    "Le unresolved",
    "Pep unresolved",
    "Ob unresolved",
    "Sic unresolved",
    "World-check unresolved",
    "World-check review required",
    "World-check/watchlist ogs",
    "Media check ogs",
    "Passport check",
    "Watchlist",
    "Media check",
    "Archived",
    "Name transposition",
    "Assignee",
    "Case created date",
    "Last modified date - user",
    "Last modified by",
    "Case created by",
    "Last screened date",
    "Last ogs modified date",
]

WANTED_COLUMNS = [
    "Case id",
    "Case name",
    "Case rating",
    "Case created date",
    "Last screened date",
]


def _parse_check_ts(folder_name: str) -> datetime | None:
    try:
        # Expected format from main.py run_dir: YYYY-MM-DD_HH-MM-SS
        return datetime.strptime(folder_name, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return None


def get_latest_check_dir(root: Path = CHECKS_ROOT) -> Path:
    """
    Return the path of the most recent check folder under BP-ON_GOING_SCREEN.

    We first parse the timestamp from the folder name, then fall back to mtime
    for folders that do not match the expected naming format.
    """
    if not root.exists():
        raise FileNotFoundError(f"Checks root not found: {root}")

    candidates: list[tuple[datetime, Path]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        ts = _parse_check_ts(entry.name)
        if ts is None:
            ts = datetime.fromtimestamp(entry.stat().st_mtime)
        candidates.append((ts, entry))

    if not candidates:
        raise FileNotFoundError(f"No check folder found in: {root}")

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _resolve_source(path: Path = PATH) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if path.is_file():
        return path

    files = [p for p in path.iterdir() if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"}]
    if not files:
        raise FileNotFoundError(f"No file found in: {path}")
    return max(files, key=lambda p: p.stat().st_mtime)


def load_ongoing_screen(path: Path = PATH, logger=None) -> pd.DataFrame:
    _debug, _log, _warn, _error = log_helpers(logger)
    try:
        source = _resolve_source(path)
        if source.suffix.lower() == ".csv":
            df = pd.read_csv(source, dtype=str, sep=",", on_bad_lines="skip")
        else:
            df = pd.read_excel(source, dtype=str)

        if len(df.columns) < len(ONGOING_COLUMNS):
            raise ValueError(
                f"On Going Screening malformed: expected at least {len(ONGOING_COLUMNS)} columns, got {len(df.columns)}"
            )

        df = df.iloc[:, : len(ONGOING_COLUMNS)].copy()
        df.columns = ONGOING_COLUMNS
        df = df[WANTED_COLUMNS]
        df = df.sort_values(by=["Last screened date"], ascending=False).reset_index(drop=True)
        df["Case name"] = (
            df["Case name"]
            .fillna("")
            .str.replace("\u00A0", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        _log(f"[ONG] Loaded {len(df)} rows from {source}")
        return df
    except Exception as exc:
        _error(f"[ONG] Failed to load screening data from {path}: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    from logger import logger as app_logger

    log = app_logger()
    _debug, _log, _warn, _error = log_helpers(log)
    df = load_ongoing_screen(logger=log)
    df["Case name"] = (
        df["Case name"]
        .fillna("")
        .str.replace("\u00A0", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    _log(f"[ONG] Loaded {len(df)} rows")
    _log(f"[ONG] Sample:\n{df.head().to_string(index=False)}")
    match = df[df["Case id"] == "5jb7pv2si9kg1k81a4g5pfb3b"]
    match["Case name"] = match["Case name"].str.strip().str.upper()
    _log(f"[ONG] Match case name: {match.iloc[0].get('Case name')}")
    _log(
        "[ONG] Exact match target: "
        f"{not match.empty and match.iloc[0].get('Case name') == 'MOUNT MERU MILLERS MOZAMBIQUE LDA'}"
    )
    _log(
        "[ONG] Rows for target case:\n"
        f"{df[df['Case name'] == 'MOUNT MERU MILLERS MOZAMBIQUE LDA'].to_string(index=False)}"
    )
