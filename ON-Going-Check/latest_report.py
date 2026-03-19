import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE_INPUT = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-ON_GOING_SCREEN")


def _parse_timestamp_dir_name(name: str) -> datetime | None:
    try:
        return datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return None


def get_latest_report_path(base_input: Path = BASE_INPUT, report_name: str | None = None) -> Optional[Path]:
    if not base_input.exists():
        return None

    dirs = [d for d in base_input.iterdir() if d.is_dir()]
    if not dirs:
        return None

    timestamped_dirs = []
    for d in dirs:
        ts = _parse_timestamp_dir_name(d.name)
        if ts is not None:
            timestamped_dirs.append((ts, d))
    while dirs:
        if timestamped_dirs:
            latest_dir = max(timestamped_dirs, key=lambda x: x[0])[1]
        else:
            latest_dir = max(dirs, key=lambda d: d.stat().st_mtime)

        if report_name:
            report_path = latest_dir / report_name
            if not report_path.exists():
                return None
            return report_path

        preferred = latest_dir / "compliance_checked.xlsx"
        if preferred.exists():
            return preferred

        print(f"didn't find {preferred} in {latest_dir}")
        timestamped_dirs = [(ts, d) for ts, d in timestamped_dirs if d != latest_dir]
        dirs = [d for d in dirs if d != latest_dir]

    return None


def load_latest_report(base_input: Path = BASE_INPUT, report_name: str | None = None) -> Optional[pd.DataFrame]:
    report_path = get_latest_report_path(base_input=base_input, report_name=report_name)
    if report_path is None:
        return None
    return pd.read_excel(
        report_path,
        dtype=str
        )


if __name__ == "__main__":
    report_path = get_latest_report_path()
    df = load_latest_report()
    if report_path is None or df is None:
        print("No latest report found.")
    else:
        print(f"Report loaded: {report_path}")
        print(f"Rows: {len(df)} | Columns: {len(df.columns)}")
