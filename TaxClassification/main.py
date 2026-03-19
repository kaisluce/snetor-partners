"""Controle de classification fiscale par SalesOrg et pays.

Entrees: KNVV, KNVI, BUT, BUT020, ADRC, Countries.
Sorties: rapports XLSX dans PATH + email si anomalies.
"""

from pathlib import Path
from datetime import datetime

import pandas as pd

from importCountries import load_countries
from importKNVI import load_knvi
from importKNVV import load_knvv
from importBUT import load_but
from importBUT020 import load_but020
from importADRC import load_adrc
from logger import logger as Logger, log_helpers
from mails import send_quality_check_mail

PATH = r"\\snetor-docs\Users\MDM\998_CHecks\BP-TAX_CLASSIFICATION"
SUBJECT = "Tax Classification"

CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe le rapport listant les partenaires avec des anomalies Tax Classification.<br>"
    "Bonne journee."
)

NO_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes les donnees Tax Classification sont conformes.<br>"
    "Bonne journee."
)


def build_kv() -> pd.DataFrame:
    # Merge KNVV (BP, SalesOrg) with KNVI (ID, country) into one table.
    knvv = load_knvv()
    knvi = load_knvi()
    kv = knvv.merge(knvi, left_on="BP", right_on="ID", how="left")
    kv = kv.drop(columns=["ID"])
    kv = kv.merge(load_but(), on="BP", how="left")
    kv = kv.merge(load_but020(), on="BP", how="left")
    kv = kv.merge(load_adrc(), on="Addr. No.", how="left")
    kv = kv[~(kv["Name"].str.startswith("#", na=False))].reset_index(drop=True)
    print(f"Total unique BPs in KV table: {kv['BP'].nunique()}")
    return kv


def bp_country_status() -> pd.DataFrame:
    # Compare expected countries per SalesOrg with actual countries per BP+SalesOrg.
    kv = build_kv()
    countries = load_countries()


    # Filter based on the countries we want to ignore

    kv = kv[kv["BP Country"] != "GR"].reset_index(drop=True)
    countries = countries[countries["Country"] != "GR"].reset_index(drop=True)
    
    kv = kv[kv["BP Country"] != "AE"].reset_index(drop=True)
    countries = countries[countries["Country"] != "AE"].reset_index(drop=True)
    
    kv = kv[kv["BP Country"] != "HR"].reset_index(drop=True)
    countries = countries[countries["Country"] != "HR"].reset_index(drop=True)
    


    expected = (
        countries.groupby("SalesOrg")["Country"]
        .apply(lambda s: set(s.dropna()))
        .to_dict()
    )
    # expected is a dict: { "FR11": {"FR", "BE", ...}, "DE10": {...}, ... }

    rows = []
    for (bp, sales_org), grp in kv.groupby(["BP", "SalesOrg"], dropna=False):
        # exp_set = set of countries that SHOULD exist for this SalesOrg
        # .get(...) returns the set if SalesOrg exists, otherwise an empty set()
        exp_set = expected.get(sales_org, set())
        # act_set = set of countries that ACTUALLY exist for this BP/SalesOrg
        mwst = grp[grp["Cond type"] == "MWST"]
        act_set = set(mwst["country"].dropna())
        # exp_set - act_set = countries expected but not found (missing)
        missing = sorted(exp_set - act_set)
        status = "ok" if not missing else "Missing one or many countries"

        # Diagnostic rules:
        # 1) Tax indicator empty -> issue
        tax_ind = grp["Tax indicator"].fillna("").astype(str).str.strip()
        has_empty_tax = (tax_ind == "").any()
        # 2) For same country: if MWST indicator == 0 but LCFR indicator != 1 -> issue
        issue_mwst_lcfr = False
        issue_mwst = False
        issue_lcfr1 = False
        lcfr_1 = False
        mwst_0_fr = False
        
        diag = []
        for country in exp_set:
            if country == "FR":
                lcfr_country = grp[(grp["country"] == country) & (grp["Cond type"] == "LCFR")]
                if lcfr_country.empty:
                    diag.append("Missing LCFR line")
            elif country == "IT":
                lcit_country = grp[(grp["country"] == country) & (grp["Cond type"] == "LCIT")]
                if lcit_country.empty:
                    diag.append("Missing LCIT line")
        for country, cgrp in grp.groupby("country", dropna=False):
            c_tax = cgrp["Tax indicator"].fillna("").astype(str).str.strip()
            has_mwst_0 = ((cgrp["Cond type"] == "MWST") & (c_tax == "0")).any()
            has_lcfr_1 = ((cgrp["Cond type"] == "LCFR") & (c_tax == "1")).any()
            if country == "FR":
                if has_mwst_0 and not has_lcfr_1:
                    mwst_0_fr = True
                    issue_mwst_lcfr = True
                    break
                elif has_mwst_0 and has_lcfr_1:
                    mwst_0_fr = True
                    lcfr_1 = True
            else:
                if has_mwst_0:
                    issue_mwst = True
                if has_lcfr_1:
                    issue_lcfr1 = True
        # 3) LCIT indicator == 1 -> issue
        lcit_bad = ((grp["Cond type"] == "LCIT") & (tax_ind == "1")).any()

        if has_empty_tax:
            diag.append("Missing one or many tax indicator")
        if issue_mwst:
            diag.append("One or many countries have MWST = 0")
        if issue_mwst_lcfr:
            diag.append("MWST = 0 and LCFR ≠ 1")
        if lcit_bad:
            diag.append("LCIT = 1")
        if issue_lcfr1:
            diag.append("LCFR = 1")
        if diag == []:
            diag.append("OK")
        rows.append(
            {
                "BP": bp,
                "Name": grp["Name"].iloc[0] if not grp["Name"].empty else "",
                "Creation date": grp["Creation date"].iloc[0] if not grp["Creation date"].empty else "",
                "Created by": grp["Created by"].iloc[0] if not grp["Created by"].empty else "",
                "Addr. No.": grp["Addr. No."].iloc[0] if not grp["Addr. No."].empty else "",
                "BP Country": grp["BP Country"].iloc[0] if not grp["BP Country"].empty else "",
                "SalesOrg": sales_org,
                "Country Diag": status,
                "Missing Countries": ",".join(missing),
                "Missing LCFR": "Missing LCFR line" in diag,
                "Missing LCIT": "Missing LCIT line" in diag,
                "Empty Tax Indicator": has_empty_tax,
                "MWST=0": issue_mwst,
                "MWST=0 LCFR!=1": issue_mwst_lcfr,
                "LCIT=1": lcit_bad,
                "LCFR=1": lcfr_1 or issue_lcfr1,
                "MWST=0 FR": mwst_0_fr,
                "Tax Diag": ",".join(diag),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["SalesOrg", "BP"]).reset_index(drop=True)
    return df


def main() -> None:
    log = Logger(mail=True, subject=SUBJECT, path=__file__)
    _debug, _log, _warn, _error = log_helpers(log)
    _log("Start tax classification check")
    try:
        status = bp_country_status()

        # Dossier par execution pour historiser les controles.
        run_folder = Path(PATH) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_folder.mkdir(parents=True, exist_ok=True)

        full_path = run_folder / "tax_classification_full.xlsx"
        diag_ko_path = run_folder / "tax_classification_diag_ko.xlsx"

        diag_ko = status[
            (status["Country Diag"].fillna("").str.lower() != "ok")
            | (status["Tax Diag"].fillna("") != "OK")
        ].copy()
        
        country_ignore_list = [["GR", "57-58"], ["AE", "60-61"], ["HR", "63-64"]]
        for country, lines in country_ignore_list:
            raw_row = {
                "BP" : "ignored country",
                "Name" : country,
                "Creation date" : f"lines to delete : {lines}",
                "Created by" : "+ delete country and lines to update from line 186",
                "Addr. No." : "file to edit : main.py",
                }
            row = pd.DataFrame([raw_row])
            status = pd.concat([status, row], ignore_index=True)
        
        status.to_excel(full_path, index=False)

        diag_ko.to_excel(diag_ko_path, index=False)

        _log(f"Saved full report: {full_path}")
        _log(f"Saved diag KO report: {diag_ko_path}")

        has_issue = not diag_ko.empty
        send_quality_check_mail(
            subject=SUBJECT,
            body=CHANGE_TEMPLATE if has_issue else NO_CHANGE_TEMPLATE,
            file_path=diag_ko_path if has_issue else None,
            logger=log,
        )
        _log("Email sent")
    except Exception:
        _error("Failure during tax classification check", exc_info=True)
        raise


if __name__ == "__main__":
    main()
