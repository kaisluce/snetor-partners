"""Controle des conditions de paiement entre KNB1 et KNVV.

Entrees: KNB1, KNVV, BUT00.
Sortie: fichier PAYEMENTS_YYYYMMDD_HHMMSS.xlsx dans le dossier courant.
"""
from datetime import datetime
from pathlib import Path

from importBUT00 import load_but00
from importKNB1 import load_knb1
from importKNVV import load_knvv

from mails import send_quality_check_mail
from logger import logger, log_helpers

BASE_DIR = Path(__file__).resolve().parent


def build_payment_check():
    knb1 = load_knb1()
    knvv = load_knvv()
    but00 = load_but00()

    # A customer can have multiple BUT rows: keep one merge key by aggregating names.
    but00_names = (
        but00.groupby("Customer", as_index=False)["Name"]
        .agg(lambda s: " | ".join(sorted({x for x in s if str(x).strip() != ""})))
    )

    df = knb1.merge(
        knvv[
            [
                "partner_id_org_com",
                "SalesOrg",
                "Created By KNVV",
                "Created On KNVV",
                "Terms of Payment KNVV",
            ]
        ],
        on="partner_id_org_com",
        how="left",
    )

    df = df.merge(but00_names, on="Customer", how="left")
    df = df[~df["Name"].fillna("").str.startswith("#", na=False)].reset_index(drop=True)

    # Diagnostic: compare Terms of Payment between company code (KNB1) and sales (KNVV).
    df["Terms of Payment"] = df["Terms of Payment"].fillna("Missing")
    df["Terms of Payment KNVV"] = df["Terms of Payment KNVV"].fillna("Missing")
    df["Terms Match"] = df["Terms of Payment"] == df["Terms of Payment KNVV"]
    df["Terms Match"] = df["Terms Match"].where(
        (df["Terms of Payment"] != "Missing") & (df["Terms of Payment KNVV"] != "Missing"),
        "Missing",
    )
    if "Name" in df.columns:
        ordered_cols = ["Customer", "Name"] + [c for c in df.columns if c not in {"Customer", "Name"}]
        df = df.reindex(columns=ordered_cols)
    return df.sort_values(by=["Customer", "Company Code"]).reset_index(drop=True)


def main() -> None:
    df = build_payment_check()
    output = BASE_DIR / f"PAYEMENTS_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df.to_excel(output, index=False)
    print(f"Saved: {output}")
    print(f"Rows: {len(df)}")


if __name__ == "__main__":
    main()
