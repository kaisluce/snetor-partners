from __future__ import annotations

"""
Genere un fichier Excel de controle des roles clients (CUSTOMER_ROLE).

Objectif
--------
Comparer l'UKM "credit vue" avec KNB1 et BUT000 pour identifier :
- les clients manquants dans KNB1,
- les clients presents dans KNB1 mais absents de l'UKM,
- et filtrer les entites interco SNETOR.

Sources
-------
- UKM (importExport.load_export) : colonnes Customer, SalesOrg, Limit Valid To
- KNB1 (importKNB1.load_knb1) : colonnes Customer, SalesOrg, Created By/On KNB1
- BUT000 (importBUT00.load_but00) : colonne Name pour filtrage

Sortie
------
Un Excel date dans le dossier CustomerRole, et un DataFrame pret pour analyse.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from mails import send_quality_check_mail
from importBUT00 import load_but00
from importKNB1 import load_knb1
from importUKM import load_ukm
from logger import logger as AppLogger, log_helpers

BASE_DIR = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-CREDIT_VUE")

SNETOR_ENTITY: set[str] = {
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
    "Vous trouverez en piece jointe le rapport listant les clients avec des anomalies Credit Vue."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les donnees Credit Vue sont conformes."
)
SUBJECT = "Credit Vue"

def _is_snetor_name(series: pd.Series) -> pd.Series:
    """
    Retourne un masque booleen des lignes dont le nom contient une entite SNETOR.

    La comparaison est faite en majuscules et ignore les blancs (match "contains").
    """
    name_up = series.fillna("").astype(str).str.strip().str.upper()
    interco_names_up = [x.strip().upper() for x in SNETOR_ENTITY if str(x).strip() != ""]
    mask = pd.Series(False, index=series.index)
    for interco_name in interco_names_up:
        mask = mask | name_up.str.contains(interco_name, regex=False, na=False)
    return mask


def build_customer_role_df(logger=None) -> pd.DataFrame:
    """
    Construit le DataFrame "Customer Role" a partir des sources UKM/KNB1/BUT000.

    Etapes principales
    - Charge UKM, KNB1 et BUT000.
    - Merge UKM/KNB1 (outer) sur la cle `customer_salesorg`.
    - Conserve un couple Customer/SalesOrg de reference et enrichit avec BUT000.
    - Calcule un diagnostic : OK, missing knb1 entry, missing credit vue.
    - Filtre les lignes archivées (#), les entites SNETOR et les clients hors perimetre.
    """
    _debug, _log, _warn, _error = log_helpers(logger)
    ukm = load_ukm()
    ukm["Present in UKM"] = True
    but00 = load_but00()
    knb1 = load_knb1()
    _log(
        f"Loaded sources: UKM={len(ukm)}, KNB1={len(knb1)}, BUT000={len(but00)}"
    )
    knb1["Present in KNB1"] = True
    merged = ukm.merge(
        knb1,
        on=["Customer", "Company Code"],
        how="outer",
    )
    merged = merged.merge(but00, on="Customer", how="left")
    merged["Present in KNB1"] = merged["Present in KNB1"].fillna(False).infer_objects(copy=False)
    merged["Present in UKM"] = merged["Present in UKM"].fillna(False).infer_objects(copy=False)
    merged["Diag"] = "OK"
    merged.loc[~merged["Present in KNB1"], "Diag"] = "missing knb1 entry"
    merged.loc[merged["Present in KNB1"] & ~merged["Present in UKM"], "Diag"] = "missing credit vue"
    merged = merged[~merged["Name"].str.startswith("#", na=False)].reset_index(drop=True)
    merged = merged[~_is_snetor_name(merged["Name"])].reset_index(drop=True)
    merged = merged[merged["Customer"].astype(str).str.startswith("1", na=False)].reset_index(drop=True)
    merged = merged[merged["Customer"].str.len() == 7]
    ordered_cols = [
        "Customer",
        "Name",
        "Company Code",
        "Limit Valid To",
        "Created By KNB1",
        "Created On KNB1",
        "Present in UKM",
        "Present in KNB1",
        "Diag",
    ]
    existing_cols = [c for c in ordered_cols if c in merged.columns]
    remaining_cols = [c for c in merged.columns if c not in existing_cols]
    merged = merged[existing_cols + remaining_cols]
    _log(f"DataFrame built with {len(merged)} rows.")
    return merged


def main() -> None:
    """Point d'entree : genere les exports CUSTOMER_ROLE et envoie le mail de reporting."""
    log = AppLogger(mail=True, path=__file__, subject=SUBJECT)
    _debug, _log, _warn, _error = log_helpers(log)

    try:
        _log("Starting Customer Vue check.")
        # Dossier par execution pour historiser les controles.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = BASE_DIR / f"customer_vue_check_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        # Create the report
        df = build_customer_role_df(logger=log)
        issue_df = df[df["Diag"] != "OK"].reset_index(drop=True)

        # Saves the issue report separatly from the full and sends it by mail if exists else sends mail with no attachement
        full_output = run_dir / "01_customer_vue_full.xlsx"
        issue_output = run_dir / "02_customer_vue_issues.xlsx"
        df.to_excel(full_output, index=False)
        _log(f"Saved full output: {full_output}")
        _log(f"Rows: full={len(df)}, issue={len(issue_df)}")

        if len(issue_df) > 0:
            issue_df.to_excel(issue_output, index=False)
            _log(f"Saved issue output: {issue_output}")
            _log("Sending report email with issue attachment.")
            send_quality_check_mail(
                subject=SUBJECT,
                body=CHANGE_TEMPLATE,
                file_path=issue_output,
                logger=log,
            )
        else:
            _log("No issue found, sending no-change email.")
            send_quality_check_mail(
                subject=SUBJECT,
                body=NO_CHANGE_TEMPLATE,
                logger=log,
            )

        _log("Customer Vue check completed.")
    except Exception as exc:
        _error(f"Customer Vue check failed: {exc}")
        raise


if __name__ == "__main__":
    main()
