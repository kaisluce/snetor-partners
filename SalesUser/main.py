from importBUT00 import load_but00
from importUSER_GPMSAL import load_user_gpmsal
from importSalesGroup import import_sales_group
from importKNVV import load_knvv
from mails import send_quality_check_mail
from logger import logger as AppLogger, log_helpers

import pandas as pd
from pathlib import Path
from datetime import datetime

SAVE_PATH = r"\\snetor-docs\Users\MDM\998_CHecks\BP-SALES_USER"
SUBJECT = "Sales User"

CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe le rapport listant les partenaires avec des anomalies Sales User.<br>"
    "Bonne journee."
)

NO_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes les donnees Sales User sont conformes.<br>"
    "Bonne journee."
)

def _normalize_users(value) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        raw = value
    elif isinstance(value, str):
        raw = value.split(",")
    else:
        raw = [value]

    cleaned = []
    for item in raw:
        if item is None or (isinstance(item, float) and pd.isna(item)):
            continue
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned

    
def main():
    log = AppLogger(mail=True, subject=SUBJECT, path=__file__)
    _debug, _log, _warn, _error = log_helpers(log)

    try:
        _log("Starting Sales User consistency check.")
        but00 = load_but00()
        user_gpmsal = load_user_gpmsal()
        sales_group = import_sales_group()
        knvv = load_knvv()
        _log(
            f"Loaded sources: BUT00={len(but00)}, GPMSAL={len(user_gpmsal)}, "
            f"SalesGroupMatrix={len(sales_group)}, KNVV={len(knvv)}"
        )

        # Align merge key dtype/format on both sides (Excel often loads numeric Sales Group as int64).
        knvv["Sales Group"] = knvv["Sales Group"].fillna("").astype(str).str.strip().str.upper()
        sales_group["Sales Group"] = sales_group["Sales Group"].fillna("").astype(str).str.strip().str.upper()
        sales_group["Affected User"] = sales_group["Affected User"].str.split("_x000D_")

        df = knvv.merge(but00, on="BP", how="left")
        df = df.merge(sales_group, on="Sales Group", how="left")
        df = df.apply(lambda row: check_sales_group_consistency(row, user_gpmsal), axis=1)

        preferred_order = [
            "BP",
            "Name",
            "Created By (KNVV)",
            "Created On (KNVV)",
            "SalesOrg",
            "Sales Group",
            "Affected User",
            "gpmsal users",
            "missing users",
            "extra users",
            "No Sales Group and no GPMSAL user",
        ]
        ordered_cols = [c for c in preferred_order if c in df.columns]
        remaining_cols = [c for c in df.columns if c not in ordered_cols]
        df = df[ordered_cols + remaining_cols]
        df = df.sort_values(by=["BP", "SalesOrg"]).reset_index(drop=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(SAVE_PATH) / f"sales_user_check_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)

        def _non_empty(col: pd.Series) -> pd.Series:
            return col.fillna("").astype(str).str.strip() != ""

        has_extra_or_missing = _non_empty(df.get("extra users", pd.Series(index=df.index, dtype=str))) | _non_empty(
            df.get("missing users", pd.Series(index=df.index, dtype=str))
        )
        has_error = _non_empty(df.get("Consistency Check Error", pd.Series(index=df.index, dtype=str)))
        no_sales_true = df.get("No Sales Group and no GPMSAL user", pd.Series(False, index=df.index)).fillna(False) == True

        combined_mask = has_extra_or_missing | has_error | no_sales_true
        issue_count = int(combined_mask.sum())

        full_file = output_dir / "01_sales_user_consistency_full.xlsx"
        issue_file = output_dir / "02_sales_user_consistency_issue.xlsx"
        df.to_excel(full_file, index=False)
        df[combined_mask].to_excel(issue_file, index=False)
        _log(f"Saved outputs in: {output_dir}")
        _log(f"Rows: full={len(df)}, issue={issue_count}")

        if issue_count > 0:
            _log("Sending report email with issue attachment.")
            send_quality_check_mail(
                subject=SUBJECT,
                body=CHANGE_TEMPLATE,
                file_path=issue_file,
                logger=log,
            )
        else:
            _log("No issue found, sending no-change email.")
            send_quality_check_mail(
                subject=SUBJECT,
                body=NO_CHANGE_TEMPLATE,
                logger=log,
            )

        _log("Sales User consistency check completed.")
    except Exception as e:
        _error(f"Sales User consistency check failed: {e}", exc_info=True)
        raise
    
def check_sales_group_consistency(row: pd.Series, gpmsal: pd.DataFrame) -> pd.Series:
    try:
        users = _normalize_users(gpmsal[gpmsal["BP"] == row["BP"]]["Affected User"].tolist())
        row_users = _normalize_users(row.get("Affected User"))

        missing_users = [user for user in row_users if user not in users]
        extra_users = [user for user in users if user not in row_users]

        row["No Sales Group and no GPMSAL user"] = (not users and not row_users)
        row["Affected User"] = ", ".join(row_users)
        row["gpmsal users"] = ", ".join(users)
        row["missing users"] = ", ".join(missing_users)
        row["extra users"] = ", ".join(extra_users)
        return row
    except Exception as e:
        print(f"Error checking sales group consistency for BP {row['BP']}: {e}")
        print(f"Users: {users}, Row Users: {row_users}")
        row["Consistency Check Error"] = str(e)
        return row
    
    
if __name__ == "__main__":
    main()
