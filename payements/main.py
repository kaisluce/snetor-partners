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

BASE_DIR = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-TERMS_OF_PAYMENT_CLIENT")

SUBJECT = "Cient Terms of Payment"

CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe le rapport listant les clients dont les conditions de paiement KNB1 et KNVV ne correspondent pas.<br>"
    "Bonne journee."
)

NO_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes les conditions de paiement KNB1 / KNVV sont conformes.<br>"
    "Bonne journee."
)


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
        knvv,
        left_on=["Customer", "Company Code"],
        right_on=["Customer", "SalesOrg"],
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
    log = logger(mail=True, subject=SUBJECT, path=__file__)
    _, log, _, error = log_helpers(log)
    log("Start payment check")
    try:
        df = build_payment_check()

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = BASE_DIR / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        output = run_dir / "payements.xlsx"
        issue_output = run_dir / "payements_issue.xlsx"

        df.to_excel(output, index=False)
        issue_df = df[~(df["Terms Match"] == True)]
        issue_df.to_excel(issue_output, index=False)

        log(f"Saved full report: {output}")
        log(f"Saved issue report: {issue_output} ({len(issue_df)} rows)")
        log(f"Total rows: {len(df)}")

        has_issues = not issue_df.empty
        send_quality_check_mail(
            subject=SUBJECT,
            body=CHANGE_TEMPLATE if has_issues else NO_CHANGE_TEMPLATE,
            file_path=issue_output if has_issues else None,
            logger=log,
        )
        log("Email sent")
    except Exception:
        error("Failure during payment check", exc_info=True)
        raise


if __name__ == "__main__":
    main()
