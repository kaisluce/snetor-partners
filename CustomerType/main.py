from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from mails import send_quality_check_mail
from importADRC import load_adrc
from importBUT000 import load_but000
from importBUT020 import load_but020_main_addr
from importKNVV import load_knvv
from logger import log_helpers, logger as Logger

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-ACCOUNT_ASSIGNMENT")

CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires avec un Customer Type mal renseigne."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les assignations Customer Type sont conformes."
)

SUBJECT = "Customer Assignement"

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

EU_COUNTRIES: set[str] = {
    "DE",
    "AT",
    "BE",
    "BG",
    "CY",
    "HR",
    "DK",
    "ES",
    "EE",
    "FI",
    "GR",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "CZ",
    "RO",
    "SK",
    "SI",
    "SE",
    "HU"
}

# Placeholder mapping: fail cleanly if unknown SalesOrg exists in source.
SALESORG_COUNTRY: dict[str, str] = {
    "FR11": "FR",
    "FR12": "FR",
    "FR13": "FR",
    "FR14": "FR",
    "GB11": "GB",
}

EXPECTED_AK_BY_TYPE: dict[str, str] = {
    "Domestic": "1",
    "UE": "2",
    "Interco": "9",
    "Export": "3",
}
CURRENT_TYPE_BY_AK: dict[str, str] = {v: k for k, v in EXPECTED_AK_BY_TYPE.items()}


def build_customer_type_df(strict_salesorg_mapping: bool = True) -> pd.DataFrame:
    knvv = load_knvv()
    print(f"[INFO] KNVV rows: {len(knvv)}")

    but000 = load_but000()
    df = knvv.merge(but000, left_on="Customer", right_on="BP", how="left")
    df = df.drop(columns=["BP"])
    print(f"[INFO] After BUT000 merge: {len(df)} rows")

    before_name_filter = len(df)
    df = df[~df["Name"].fillna("").str.startswith("#", na=False)].reset_index(drop=True)
    if "Search Term 1" in df.columns:
        df = df[~df["Search Term 1"].str.startswith("#", na=False)]
    else :
        print("Missing column 'Search Term 1' in dataframe")
    print(f"[INFO] Name '#' filter removed: {before_name_filter - len(df)} rows")

    but020 = load_but020_main_addr()
    adrc = load_adrc()
    address_country = but020.merge(adrc, on="Addr. No.", how="left")
    df = df.merge(address_country[["BP", "BP Country"]], left_on="Customer", right_on="BP", how="left")
    df = df.drop(columns=["BP"])
    print(f"[INFO] After address/country merge: {len(df)} rows")

    salesorg_country = df["SalesOrg"].map(SALESORG_COUNTRY)
    unknown_salesorg = sorted(df.loc[salesorg_country.isna(), "SalesOrg"].dropna().unique().tolist())
    print(f"[INFO] Unknown SalesOrg mapping count: {len(unknown_salesorg)}")
    if unknown_salesorg and strict_salesorg_mapping:
        raise ValueError(
            "Unknown SalesOrg country mapping for: "
            + ", ".join(unknown_salesorg[:20])
            + (" ..." if len(unknown_salesorg) > 20 else "")
        )

    interco_names_up = [x.strip().upper() for x in INTERCO_NAMES if str(x).strip() != ""]
    name_up = df["Name"].fillna("").astype(str).str.strip().str.upper()
    country = df["BP Country"].fillna("").astype(str).str.strip().str.upper()

    # Interco if one reference company name is contained in Name (not exact match required).
    is_interco = pd.Series(False, index=df.index)
    for interco_name in interco_names_up:
        is_interco = is_interco | name_up.str.contains(interco_name, regex=False, na=False)
    is_unknown_so = salesorg_country.isna()
    is_missing_country = country == ""
    is_domestic = country == salesorg_country.fillna("")
    is_ue = country.isin(EU_COUNTRIES)

    expected_type = pd.Series(pd.NA, index=df.index, dtype="object")

    # Precedence used here: Interco > unknown SalesOrg > missing country > Domestic > UE > Export.
    mask = is_interco
    expected_type.loc[mask] = "Interco"

    mask = (~is_interco) & is_unknown_so

    mask = (~is_interco) & (~is_unknown_so) & is_missing_country

    mask = (~is_interco) & (~is_unknown_so) & (~is_missing_country) & is_domestic
    expected_type.loc[mask] = "Domestic"

    mask = (~is_interco) & (~is_unknown_so) & (~is_missing_country) & (~is_domestic) & is_ue
    expected_type.loc[mask] = "UE"

    mask = (~is_interco) & (~is_unknown_so) & (~is_missing_country) & (~is_domestic) & (~is_ue)
    expected_type.loc[mask] = "Export"
    df["Expected type"] = expected_type
    df["Current type"] = df["Account Assgn. Grp. Current"].map(CURRENT_TYPE_BY_AK)
    df["Account Assgn. Grp. Expected"] = df["Expected type"].map(EXPECTED_AK_BY_TYPE)
    df["Account Assgn. Grp. Status"] = np.where(
        df["Account Assgn. Grp. Current"] == df["Account Assgn. Grp. Expected"], "OK", "Missmatch"
    )

    missing_current = df["Account Assgn. Grp. Current"].fillna("").astype(str).str.strip() == ""
    missing_country = df["BP Country"].fillna("").astype(str).str.strip() == ""
    mismatch = (
        ~missing_current
        & df["Account Assgn. Grp. Expected"].notna()
        & (df["Account Assgn. Grp. Current"] != df["Account Assgn. Grp. Expected"])
    )

    df.loc[mismatch, "Account Assgn. Grp. Status"] = "Missmatch"
    df.loc[missing_country, "Account Assgn. Grp. Status"] = "Missing country code"
    df.loc[missing_current, "Account Assgn. Grp. Status"] = "Missing Asign. grp"

    result = df[
        [
            "Customer",
            "SalesOrg",
            "Name",
            "Created By KNVV",
            "Creation Date KNVV",
            "BP Country",
            "Current type",
            "Account Assgn. Grp. Current",
            "Expected type",
            "Account Assgn. Grp. Expected",
            "Account Assgn. Grp. Status",
        ]
    ].copy()

    print(f"[INFO] Final rows: {len(result)}")
    return result


def main() -> None:
    app_logger = Logger(mail=True, subject=SUBJECT, path=__file__)
    _debug, log, _warn, error = log_helpers(app_logger)
    log("Start account assignment check")
    try:
        df = build_customer_type_df(strict_salesorg_mapping=True)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = OUTPUT_ROOT / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        full_xlsx = run_dir / "account_assignment_full.xlsx"
        issues_xlsx = run_dir / "account_assignment_issues.xlsx"

        df.to_excel(full_xlsx, index=False)
        issues = df[df["Account Assgn. Grp. Status"] != "OK"].copy()
        issues.to_excel(issues_xlsx, index=False)

        log(f"Saved full output: {full_xlsx}")
        log(f"Saved issues output: {issues_xlsx}")
        log(f"Full rows: {len(df)} | Issue rows: {len(issues)}")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            send_quality_check_mail(
                subject=SUBJECT,
                body=CHANGE_TEMPLATE if not issues.empty else NO_CHANGE_TEMPLATE,
                file_path=str(issues_xlsx) if not issues.empty else None,
                logger=app_logger,
            )
        log("Email sent")
    except Exception:
        error("Failure during account assignment check", exc_info=True)
        raise


if __name__ == "__main__":
    main()
