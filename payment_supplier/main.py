"""Controle des conditions de paiement entre LFM1 et LFB1.

Entrees: LFB1, LFB1, BUT00.
Sortie: fichier PAYEMENTS_YYYYMMDD_HHMMSS.xlsx dans le dossier courant.
"""

from datetime import datetime
from pathlib import Path

from import_BUT import load_but
from import_LFB1 import load_lfb1
from import_LFM1 import load_lfm1

from mails import send_quality_check_mail
from logger import logger, log_helpers

BASE_DIR = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-TERMS_OF_PAYMENT_SUPPLIER")

SUBJECT = "Supplier Terms of Payment"

ISSUE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les fournisseurs dont les conditions de paiement LFB1 et LFM1 ne correspondent pas.<br>"
    "Bonne journee."
)

NO_ISSUE_TEMPLATE = (
    "Toutes les conditions de paiement LFB1 / LFM1 sont conformes.<br>"
    "Bonne journee."
)


def main()-> None:
    def build_merged():
        def get_but00():
            log("Loading BUT00")
            return load_but()

        def get_lfb1():
            log("Loading LFB1")
            return load_lfb1()

        def get_lfm1():
            log("Loading LFM1")
            return load_lfm1()
        
        log("Fetching datas...")
        
        but = get_but00()
        lfb1 = get_lfb1()
        lfm1 = get_lfm1()

        merged_lfb1_lfm1 = lfb1.merge(lfm1, on=["Supplier", "Company Code"], how="left")
        merged_all = merged_lfb1_lfm1.merge(but, on="Supplier", how="left")
        
        merged_all = merged_all[merged_all["Name"].str.startswith("#", na = False) == False]
        
        log(f"Merged all datas, final rows: {len(merged_all)}")
        
        return merged_all
    
    def reorder_columns(df):
        new_order = [
            "Supplier",
            "Company Code",
            "Name",
            "Created On LFB1",
            "Created By LFB1",
            "Created On LFM1",
            "Created By LFM1",
            "Terms of Payment LFB1",
            "Terms of Payment LFM1",
            "Terms Match",
        ]
        
        return df.reindex(columns=new_order)
    
    log = logger(mail=True, subject=SUBJECT, path=__file__)
    _, log, _, error = log_helpers(log)
    log("Start payment check")
    
    try:
        df = build_merged()
        
        # filling missing entries for payments terms
        log("Filling missing entries")
        df["Terms of Payment LFB1"] = df["Terms of Payment LFB1"].fillna("Missing")
        df["Terms of Payment LFM1"] = df["Terms of Payment LFM1"].fillna("Missing")
        
        # checks if both fields are equals
        log("Checking terms")
        df["Terms Match"] = (df["Terms of Payment LFB1"] == df["Terms of Payment LFM1"]).astype(object)
        
        # treats the case where one of the fields are missing
        log("Treating missing terms")
        mask_missing_lfb1 = df["Terms of Payment LFB1"] == "Missing"
        mask_missing_lfm1 = df["Terms of Payment LFM1"] == "Missing"
        df.loc[mask_missing_lfb1 & ~mask_missing_lfm1, "Terms Match"] = "Missing LFB1 Term"
        df.loc[~mask_missing_lfb1 & mask_missing_lfm1, "Terms Match"] = "Missing LFM1 Term"
        df.loc[mask_missing_lfb1 & mask_missing_lfm1, "Terms Match"] = "Missing LFB1 and LFM1 Terms"
        
        log("Reordering columns for output")
        result_df = reorder_columns(df)
        
        log("Saving output")
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = BASE_DIR / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        output = run_dir / "suppliers_payements.xlsx"
        issue_output = run_dir / "suppliers_payements_issue.xlsx"

        result_df.to_excel(output, index=False)
        issue_df = result_df[~(result_df["Terms Match"] == True)]
        issue_df.to_excel(issue_output, index=False)

        log(f"Saved full report: {output}")
        log(f"Saved issue report: {issue_output} ({len(issue_df)} rows)")
        log(f"Total rows: {len(result_df)}")

        has_issues = not issue_df.empty
        send_quality_check_mail(
            subject=SUBJECT,
            body=ISSUE_TEMPLATE if has_issues else NO_ISSUE_TEMPLATE,
            file_path=issue_output if has_issues else None,
            logger=log,
        )
        log("Email sent")
    except Exception:
        error("Failure during payment check", exc_info=True)
        raise
    
if __name__ == "__main__":
    main()