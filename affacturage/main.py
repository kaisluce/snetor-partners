"""Controle affacturage (AR pledging) pour clients KNB1.

Entrees: KVV, BUT00, KNB1.
Sortie: exports Excel dans un dossier de run horodate.
"""

import asyncio
from datetime import datetime
from pathlib import Path

import pandas as pd

from mails import send_quality_check_mail
from importBUT00 import load_but00
from importKNB1 import load_knb1
from logger import logger as AppLogger, log_helpers

BASE_DIR = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-AFFACTURAGE")

INTERCO_NAMES: set[str] = {
    "SNETOR",
    "SNETOR OVERSEAS",
    "SNETOR MAROC",
    "EIXO SNETOR BRASIL",
    "SNETOR ECUADOR",
    "SNETOR FRANCE",
    "OZYANCE",
    "SNETOR KOREA",
    "SNETOR EGYPT",
    "SNETOR SOUTH AFRICA",
    "SNETOR COLOMBIA",
    "SNETOR CHILE",
    "SNETOR UK LTD",
    "TECNOPOL SNETOR ITALIA",
    "SNETOR SHANGHAI",
    "SNETOR WEST AFRICA LTD",
    "SNETOR EAST AFRICA",
    "SNETOR PERU",
    "SNETOR USA",
    "SNETOR BENELUX",
    "OZYANCE ITALIA",
    "SNETOR DISTRIBUTION UGANDA",
    "SNETOR MIDDLE EAST",
    "COANSA SNETOR COSTA RICA",
    "COANSA SNETOR EL SALVADOR",
    "SNETOR NORDEN",
    "LEONARDI",
    "SNETOR MUSQAT",
    "COANSA SNETOR GUATEMALA",
    "SNETOR MEXICO",
    "SNETOR GERMANY GMBH",
    "TECNOPOL SNETOR IBERIA",
    "SNETOR EASTERN EUROPE",
    "SNETOR BALKAN",
    "MEG SNETOR TURKIYE",
    "SNETOR LOGISTICS",
}


CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires dont l'affacturage est mal renseigne."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les donnees liées à l'AR Pledging sont conformes."
)

SUBJECT = "Missing AR Pledging FF"

def build_affacturage_df() -> pd.DataFrame:

    but00 = load_but00().drop_duplicates(subset=["BP"]).reset_index(drop=True)
    but00 = but00.rename(columns={"BP": "Customer"})

    knb1 = load_knb1()
    knb1 = knb1[knb1["Customer"].str.startswith("1", na=False)].reset_index(drop=True)
    knb1 = knb1.drop_duplicates(subset=["Customer"]).reset_index(drop=True)

    # Main table: keep all KNB1 lines, enrich with BUT00 data.
    df = knb1.merge(but00[["Customer", "Name"]], on="Customer", how="left")
    
    df = df[~df["Name"].str.startswith("#", na=False)].reset_index(drop=True)
    df = df[~df["Name"].isin(INTERCO_NAMES)].reset_index(drop=True)
    df = df[~(df["Name"].str.upper().str.contains("SNETOR", na=False))].reset_index(drop=True)
    df = df[~(df["Name"].str.upper().str.contains("OZYANCE", na=False))].reset_index(drop=True)
    df = df[~(df["Name"].str.upper().str.contains("LEONARDI", na=False))].reset_index(drop=True)

    # Diagnostic A/R pledging: Missing / FF / autres valeurs.
    ar = df["AR Pledging Ind."].fillna("").str.strip().str.upper()
    df["AR Planning Diag"] = "OK"
    df.loc[ar == "", "AR Planning Diag"] = "Missing"
    df.loc[(ar != "") & (ar != "FF"), "AR Planning Diag"] = "Incorrect"
    df["In BUT00"] = df["Name"].notna()

    df = df.sort_values(by=["Customer"]).reset_index(drop=True)
    return df


def main() -> None:
    log = AppLogger(mail=True, path = __file__, subject=SUBJECT)
    _debug, _log, _warn, _error = log_helpers(log)

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = BASE_DIR / f"affacturage_check_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        _log("Starting affacturage check.")
        df = build_affacturage_df()

        full_output = run_dir / "01_affacturage_full.xlsx"
        issue_output = run_dir / "02_affacturage_issues.xlsx"
        df.to_excel(full_output, index=False)

        issue_df = df[
            (df["AR Planning Diag"] != "OK")
            | (df["In BUT00"] == False)
        ].reset_index(drop=True)
        _log(f"Saved outputs in: {run_dir}")
        _log(f"Rows: full={len(df)}, issue={len(issue_df)}")

        if len(issue_df) > 0:
            issue_df.to_excel(issue_output, index=False)
            _log("Sending report email with issue attachment.")
            send_quality_check_mail(subject = SUBJECT, body=CHANGE_TEMPLATE, file_path=issue_output, logger=log)
        else:
            _log("No issue found, sending no-change email.")
            send_quality_check_mail(subject = SUBJECT, body=NO_CHANGE_TEMPLATE, logger=log)

        _log("affacturage check completed.")
    except Exception as exc:
        _error(f"affacturage check failed: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
