"""Tax-Exemption baseline workflow.

Inputs: KNVV, KNVI, BUT000, BUT020, ADRC, Countries.
Output: consolidated dataframe for exemption analysis.
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from mails import send_quality_check_mail
from logger import log_helpers, logger as Logger

from importKNVI import load_knvi
from importKNVV import load_knvv
from importBUT import load_but
from importBUT020 import load_but020
from importADRC import load_adrc


FILES_BASE_PATH = Path(r"\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\001_Customer\Exemption")

SAVE_PATH = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-TAX_EXEMPTION")
SUBJECT = "Tax Exemption"

CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires avec des anomalies Tax Exemption.<br>"
    "Bonne journee."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les donnees Tax Exemption sont conformes.<br>"
    "Bonne journee."
)


def build_kv(app_logger=None) -> pd.DataFrame:
    _debug, log, _warn, _error = log_helpers(app_logger)
    # Build the customer reference table by consolidating SAP sources.
    # KNVV: sales setup, KNVI: tax data, BUT/BUT020/ADRC: identity + address.
    knvv = load_knvv(logger=app_logger)
    knvi = load_knvi(logger=app_logger)
    kv = knvv.merge(knvi, left_on="BP", right_on="ID", how="left")
    kv = kv.drop(columns=["ID"])
    kv = kv.merge(load_but(logger=app_logger), on="BP", how="left")
    kv = kv.merge(load_but020(logger=app_logger), on="BP", how="left")
    kv = kv.merge(load_adrc(logger=app_logger), on="Addr. No.", how="left")
    # Ignore technical/marked entries (name starting with '#').
    kv = kv[~(kv["Name"].str.startswith("#", na=False))].reset_index(drop=True)
    log(f"Total unique BPs in KV table: {kv['BP'].nunique()}")
    return kv


def check_files(df: pd.DataFrame, app_logger=None) -> pd.DataFrame:
    _debug, _log, warn, _error = log_helpers(app_logger)

    def check_bp(name: str, year: str, salesorg: str) -> tuple[bool, bool]:
        # Expected folder structure: <base>/<year>/<salesorg>/...
        folder = FILES_BASE_PATH / year / str(salesorg)

        if not folder.exists():
            warn(f"Directory '{folder}' does not exist")
            return False, False
        if not folder.is_dir():
            warn(f"'{folder}' is not a folder")
            return False, False

        dispense, attestation = False, False
        name_upper = str(name).upper()
        # Text search across all files in the SalesOrg folder.
        for _, _, files in os.walk(folder):
            for filename in files:
                filename_upper = filename.upper()
                if name_upper in filename_upper and "ATTESTATION FRANCHISE TVA" in filename_upper:
                    attestation = True
                if name_upper in filename_upper and "DECISION DE DISPENSE" in filename_upper:
                    dispense = True

        if not dispense and not attestation:
            warn(f"No tax exemption for '{name_upper}' in '{folder}'")
        return dispense, attestation

    # Run checks against the latest available year folder.
    years = [p.name for p in FILES_BASE_PATH.iterdir() if p.is_dir()]
    if not years:
        raise FileNotFoundError(f"No year folder found in '{FILES_BASE_PATH}'")
    year = max(years)

    df[["Has dispense file", "Has attestation file"]] = df.apply(
        lambda row: pd.Series(check_bp(row["Name"], year, row["SalesOrg"])),
        axis=1,
    )

    return df
            


def main() -> None:
    app_logger = Logger(mail=True, subject=SUBJECT, path=__file__)
    _debug, log, _warn, error = log_helpers(app_logger)
    log("Start tax exemption check")
    try:
        df = build_kv(app_logger=app_logger)
        # Country fallback: fill missing "BP Country" from "country".
        df["BP Country"] = df["BP Country"].fillna(df["country"])
        # Business rule: French population with the two relevant condition types.
        french = df[df["BP Country"] == "FR"].copy()
        french = french[french["Cond type"].isin(["MWST", "LCFR"])].copy()

        # Pivot to place MWST and LCFR on a single customer row.
        french_pivot = (
            french.pivot_table(
                index=["BP", "SalesOrg", "Name", "country", "BP Country", "Creation date", "Created by"],
                columns="Cond type",
                values="Tax indicator",
                aggfunc="first",
            )
            .reset_index()
        )
        if "MWST" not in french_pivot.columns or "LCFR" not in french_pivot.columns:
            log("No MWST/LCFR combination found in pivot; result set will be empty")
            french_pivot = french_pivot.iloc[0:0].copy()
        else:
            # Expected exemption case: MWST=0 and LCFR=1.
            french_pivot = french_pivot[(french_pivot["MWST"] == "0") & (french_pivot["LCFR"] == "1")]

        french_pivot.columns.name = None

        # Timestamped run folder to keep execution history.
        run_folder = SAVE_PATH / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_folder.mkdir(parents=True, exist_ok=True)

        full_path = run_folder / "tax_exemption_data.xlsx"
        filtered_path = run_folder / "tax_exemption_results.xlsx"
        error_path = run_folder / "missing_exemption_files.xlsx"

        french_pivot.to_excel(full_path, index=False)
        # Check supporting document presence in shared folders.
        results = check_files(french_pivot.copy(), app_logger=app_logger)
        results.to_excel(filtered_path, index=False)
        # "errors" = at least one required document is missing.
        errors = results[~results[["Has dispense file", "Has attestation file"]].all(axis=1)]
        errors.to_excel(error_path, index=False)

        log(f"Rows: {len(df)}")
        log(f"Customers: {df['BP'].nunique()}")
        log(f"FR pivot rows: {len(french_pivot)}")
        log(f"Saved full report: {full_path}")
        log(f"Saved filtered report: {filtered_path}")
        log(f"Saved error report: {error_path} ({len(errors)} rows)")

        if not errors.empty:
            send_quality_check_mail(
                subject=SUBJECT,
                body=CHANGE_TEMPLATE,
                file_path=error_path,
                logger=app_logger,
            )
            log("Error report email sent")
        else:
            send_quality_check_mail(
                subject=SUBJECT,
                body=NO_CHANGE_TEMPLATE,
                logger=app_logger,
            )
            log("No-change email sent")
    except Exception:
        error("Failure during tax exemption check", exc_info=True)
        raise


if __name__ == "__main__":
    main()
