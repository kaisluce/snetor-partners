"""
Merge BUT000, BUT020 and ADRC for BP -> address -> country analysis.

Steps:
- Load BUT000 (BP, Name) and drop names starting with "#".
- Load BUT020 (BP to Addr. No. link).
- Load ADRC (Addr. No. to BP Country).
- Merge on BP, then on Addr. No.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from importADRC import load_adrc
from importBUT000 import load_but000
from importBUT020 import load_but020
from importReport import load_report_xlsx

BASE_DIR = Path(__file__).resolve().parent

DROM_CITIES = {
    # Guadeloupe
    "POINTE A PITRE",
    "LES ABYMES",
    "BAIE MAHAULT",
    "BASSE TERRE",
    "LE GOSIER",
    "SAINTE ANNE",
    # Martinique
    "FORT DE FRANCE",
    "LE LAMENTIN",
    "SAINTE ANNE",
    "SAINT PIERRE",
    # Guyane
    "CAYENNE",
    "KOUROU",
    "SAINT LAURENT DU MARONI",
    "MATOURY",
    "REMIRE MONTJOLY",
    # La Reunion
    "SAINT DENIS",
    "SAINT PAUL",
    "SAINT BENOIT",
    # Mayotte
    "MAMOUDZOU",
    "DZAOUDZI",
    "KOUNGOU",
}

DROM_COUNTRY_CODE = {
    "RE",
    "GP",
    "MQ",
    "YT",
    "GF",
    "BL",
    "MF",
    "PM",
    "WF",
    "PF",
}

def _norm_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _resolve_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lookup = {_norm_key(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_key(cand)
        if key in lookup:
            return lookup[key]
    return None


def _build_address(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in ["street", "street4", "street5", "city", "postcode", "country"] if c in df.columns]
    if not cols:
        return pd.Series([""] * len(df), index=df.index)
    cleaned = df[cols].fillna("").astype(str).apply(lambda s: s.str.strip())
    return cleaned.apply(lambda r: ", ".join([v for v in r if v != ""]), axis=1)


def build_finddrom_df() -> pd.DataFrame:
    but000 = load_but000()
    but020 = load_but020()
    adrc = load_adrc()
    report = load_report_xlsx()

    addr = but020.merge(adrc, on="Addr. No.", how="left")
    df = but000.merge(addr, on="BP", how="left")
    df = df.merge(report, on="BP", how='left')

    # Safety filter in case BUT000 is reused without the name filter.
    df = df[~df["Name"].str.startswith("#", na=False)].reset_index(drop=True)
    df = df[~df["BP"].str.startswith("5", na=False)].reset_index(drop=True)

    mask_country = (
        df["country"].fillna("").astype(str).str.strip().str.upper().isin(DROM_COUNTRY_CODE)
        if "country" in df.columns
        else pd.Series(False, index=df.index)
    )

    mask_postcode = (
        df["postcode"].fillna("").astype(str).str.match(r"^(97[1-6]|975|986|987)")
        if "postcode" in df.columns
        else pd.Series(False, index=df.index)
    )
    mask_city = (
        df["city"].fillna("").astype(str).str.strip().str.upper().isin(DROM_CITIES)
        if "city" in df.columns
        else pd.Series(False, index=df.index)
    )
    # mask_country = (
    #     df["country"].fillna("").astype(str).str.strip().str.upper() == "FR"
    #     if "country" in df.columns
    #     else pd.Series(False, index=df.index)
    # )
    code_postal_col = _resolve_col(df, ["code_postal", "codepostal", "postalcode"])
    if code_postal_col:
        mask_fetched = df[code_postal_col].fillna("").astype(str).str.match(r"^(97|975|986|987)")
    else:
        mask_fetched = pd.Series(False, index=df.index)

    drom_mask = (mask_country | mask_fetched | mask_postcode | mask_city) #& mask_country
    drompartners = df[drom_mask].copy()

    address = _build_address(drompartners)
    siren_col = _resolve_col(drompartners, ["siren"])
    siret_col = _resolve_col(drompartners, ["siret"])
    vat_col = _resolve_col(drompartners, ["vat", "tva", "vat_id", "vatid", "vat number", "no tva"])
    status_col = _resolve_col(drompartners, ["status", "statut", "etat"])
    
    country_postcode = {
    "RE" : "974",
    "GP" : "971",
    "MQ" : "972",
    "YT" : "976",
    "GF" : "973",
    "BL" : "971", # Saint-Barthelemy (97133)
    "WF" : "986", # Wallis et Futuna
    "MF" : "971", # Saint-Martin (97150)
    "PF" : "987", # Polynesie francaise
    "PM" : "975", # Saint-Pierre-et-Miquelon
    }
    
    if "country" in drompartners.columns and "postcode" in drompartners.columns:
        country_series = drompartners["country"].fillna("").astype(str).str.strip().str.upper()
        postcode_prefix = drompartners["postcode"].fillna("").astype(str).str.strip().str[:3]
        expected_prefix = country_series.map(country_postcode).fillna("")
        right_country_code = (expected_prefix != "") & (postcode_prefix == expected_prefix)
    else:
        right_country_code = pd.Series(False, index=drompartners.index)
    

    drompartners = pd.DataFrame(
        {
            "BP": drompartners.get("BP", ""),
            "Name": drompartners.get("Name", ""),
            "Address": address,
            "SIREN": drompartners[siren_col] if siren_col else "",
            "SIRET": drompartners[siret_col] if siret_col else "",
            "VAT": drompartners[vat_col] if vat_col else "",
            "Status": drompartners[status_col] if status_col else "",
            "Right country code": right_country_code,
        }
    )

    return drompartners


def main() -> None:
    df = build_finddrom_df()
    output = BASE_DIR / f"FIND_DROM_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df.to_excel(output, index=False)
    print(f"Saved: {output}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
