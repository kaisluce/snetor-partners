"""Controle langue vs pays et champs rue pour les BP.

Entrees: BP_BUT000.csv, BP_BUT020.csv, BP_ADRC.csv.
Sorties: dossier horodate sous OUTPUT_ROOT + rapports XLSX + emails si anomalies.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from lingua import Language, LanguageDetectorBuilder
from mails import send_quality_check_mail
from logger import log_helpers, logger as Logger

PATH_BUT000 = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv")
PATH_BUT020 = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT020.csv")
PATH_ADRC = Path(r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = Path(r"\\snetor-docs\Users\MDM\998_CHecks\BP-LANGUAGE_AND_STREET_CHECK")
SUBJECT_STREET = "Address Street Check"
SUBJECT_LANGUAGE = "Address Language Check"

STREET_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe la liste des BPs dont la street 2 ou 3 ne sont pas à vides.<br>"
    "Bonne journee."
)
LANGUAGE_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe le rapport des BPs avec les mauvaises Langues.<br>"
    "Bonne journee."
)
NO_ISSUES_STREET_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes aucun champ Street 2 ou 3 n'est renseigné.<br>"
    "Bonne journee."
)
NO_ISSUES_LANGUAGE_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes les langues sont conformes.<br>"
    "Bonne journee."
)



# French spaeking countries list for filtering
FRANCOPHONE_COUNTRIES: set[str] = {
    "FR", "LU", "MC", "MQ",
    "HT", "SN", "CI", "BF", "DZ",
    "BJ", "TG", "ML", "NE", "GN",
    "CM", "GA", "CG", "CD", "CF",
    "TD", "DJ", "KM", "MG", "BI",
    "RW",
    "TG", "VU", "SC", "MA", "TN",
    "RE", "YT", "GF", "MR"
}

BAD_LINES: dict[str, list[list[str]]] = {}

_BE_DETECTOR = (
    LanguageDetectorBuilder
    .from_languages(Language.FRENCH, Language.DUTCH, Language.GERMAN, Language.ENGLISH)
    .build()
)

_LINGUA_TO_SAP: dict[Language, str] = {
    Language.FRENCH: "F",
    Language.DUTCH:  "E",
    Language.GERMAN: "E",
    Language.ENGLISH: "E",
}

def _normalize_bp(series: pd.Series) -> pd.Series:
    """
    Normalizes the BP column for a safer merge
    """
    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.zfill(10)
    cleaned = cleaned.str.lstrip("0")
    return cleaned.replace("", "0")

def _normalize_addr(s: pd.Series) -> pd.Series:
    """
    Normalizes the address number column
    """
    return (
        s.fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\D", "", regex=True)  # deletes whatever is not a digit
        .str.zfill(15)
        .str.lstrip("0")
    )

def _read_csv_with_badlines(
    path: Path,
    *,
    expected_cols: int | None = None,
    pad_short_lines: bool = True,
    merge_long_lines: bool = True,
    **kwargs,
) -> pd.DataFrame:
    """
    Creates a df using a csv and prints out lines with issues
    """
    bad_lines: list[list[str]] = []

    sep = kwargs.get("sep", ",")
    encoding = kwargs.get("encoding", "utf-8")
    encoding_errors = kwargs.get("encoding_errors", "replace")

    if expected_cols is None:
        with open(path, "r", encoding=encoding, errors=encoding_errors) as f:
            header = f.readline()
        expected_cols = header.count(sep) + 1

    def _collect(line: list[str]) -> list[str] | None:
        bad_lines.append(line)
        if expected_cols:
            if pad_short_lines and len(line) < expected_cols:
                return line + [""] * (expected_cols - len(line))
            if merge_long_lines and len(line) > expected_cols:
                # preserve row by folding extra fields into the last column
                return line[: expected_cols - 1] + [sep.join(line[expected_cols - 1 :])]
        return None

    df = pd.read_csv(path, on_bad_lines=_collect, engine="python", **kwargs)
    if bad_lines:
        BAD_LINES[str(path)] = bad_lines
        print(f"[WARN] {path}: {len(bad_lines)} bad lines detected. First 2 columns:")
        for idx, line in enumerate(bad_lines, start=1):
            first_two = line[:2] + [""] * (2 - len(line))
            print(f"[WARN]   {idx}: {first_two[0]} | {first_two[1]}")
    return df



def load_but000(path: Path = PATH_BUT000) -> pd.DataFrame:
    """
    fetches the BUT 000 table
    """
    df = _read_csv_with_badlines(path, dtype=str, sep=";")
    if df.shape[1] <= 14:
        raise ValueError(
            f"BP_BUT000.csv malformed: expected at least 15 columns including Last/First Name, got {df.shape[1]}"
        )
    # Data dictionary: A=BP, H=Name, L=Last Name, M=First Name, N=Created On, O=Created By
    df = df.iloc[:, [0, 7, 11, 12, 13, 14, 19]].copy()
    df.columns = ["BP", "Name", "Last Name", "First Name", "Created On", "Created By", "Correspondence Language"]
    df["BP"] = _normalize_bp(df["BP"])
    df["Name"] = df["Name"].fillna("").astype(str).str.strip()
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    df["Created On"] = df["Created On"].fillna("").astype(str).str.strip()
    df["Created By"] = df["Created By"].fillna("").astype(str).str.strip()

    init = len(df)
    df = df[df["BP"] != ""].reset_index(drop=True)
    df = df[~df["Name"].str.startswith("#", na=False)].reset_index(drop=True)
    df = df[~df["BP"].str.startswith("9", na=False)].reset_index(drop=True)
    df = df[~df["BP"].str.startswith("5", na=False)].reset_index(drop=True)
    df = df[~df["BP"].str.startswith("29", na=False)].reset_index(drop=True)
    
    df = df[~df["BP"].isin(["10000010", "10000012"])]
    
    personnes = (df["Name"] == "") & ~((df["Last Name"] == "") & (df["First Name"] == ""))
    personnes_diez = personnes & (df["Last Name"].str.contains("#", na=False) | df["First Name"].str.contains("#", na=False))
    personnes_strt_diez = personnes_diez & df["Last Name"].str.startswith("#", na=False)
    df.loc[personnes, "Name"] = "(person)" + (df.loc[personnes, "Last Name"] + " " + df.loc[personnes, "First Name"]).str.strip()
    df = df[~personnes_diez].reset_index(drop=True)
    
    
    print(f"[INFO] BUT000 init={init}, after filters={len(df)}")
    return df


def load_but020(path: Path = PATH_BUT020) -> pd.DataFrame:
    """
    fetches the BUT 020 table
    """
    df = _read_csv_with_badlines(path, dtype=str, sep=";")
    if df.shape[1] <= 1:
        raise ValueError(f"BP_BUT020.csv malformed: expected at least 2 columns, got {df.shape[1]}")
    # Data dictionary: A=BP, B=Addr. No.
    df = df.iloc[:, [0, 1]].copy()
    df.columns = ["BP", "Addr. No."]
    df["BP"] = _normalize_bp(df["BP"])
    df["Addr. No."] = _normalize_addr(df["Addr. No."])
    idx = df.groupby("BP")["Addr. No."].idxmax()
    return df.loc[idx, ["BP", "Addr. No."]].reset_index(drop=True)


def load_adrc(path: Path = PATH_ADRC) -> pd.DataFrame:
    """
    fetches the ADRC table
    """
    df = _read_csv_with_badlines(path, dtype=str, sep=";")
    print(df.describe())
    if df.shape[1] <= 29:
        raise ValueError(f"BP_ADRC.csv malformed: expected at least 30 columns, got {df.shape[1]}")
    # User mapping: A=Addr. No., L=BP Country, T=Language, U=Street 5, AA/AB/AC/AD=Street/2/3/4
    df = df.iloc[:, [0, 11, 19, 26, 27, 28, 29, 20]].copy()
    df.columns = ["Addr. No.", "BP Country", "Language", "Street", "Street 2", "Street 3", "Street 4", "Street 5"]
    df["BP Country"] = df["BP Country"].fillna("").astype(str).str.strip().str.upper()
    return df.reset_index(drop=True)

 

def diag_BE(row: pd.Series) -> str:
    streets_list = row[["Street", "Street 2", "Street 3", "Street 4", "Street 5"]]
    streets_str = " ".join([s for s in streets_list if str(s).strip() != ""])

    if not streets_str.strip():
        return "No street found for BE diag"

    detected = _BE_DETECTOR.detect_language_of(streets_str)
    if detected is None:
        return "No language detected with street"


    expected_language = _LINGUA_TO_SAP.get(detected)
    sap_lang = str(row.get("Language", "")).strip().upper()

    if expected_language is None:
        return "No language detected with street"

    if sap_lang == expected_language:
        return "OK"
    return "Wrong Language"

def build_diagnostic_df() -> pd.DataFrame:
    """
    Merges all table together and builds the diagnostic dataframe
    """
    but000 = load_but000()
    but020 = load_but020()
    adrc = load_adrc()

    # Merges the tables with the partner informations and the address to analise the language
    addr = but020.merge(adrc, on="Addr. No.", how="outer")
    df = but000.merge(addr, on="BP", how="left")
    
    # Fetches the Language from ADRC for people
    personnes = df["Name"].str.startswith("(person)", na=False)
    df.loc[personnes, "Language"] = df.loc[personnes, "Correspondence Language"].fillna("").astype(str).str.strip().str.upper()
    df.drop(columns=["Correspondence Language"], inplace=True)

    # Checks to see if the partners has any street 2 or 3
    has_address = (df["Addr. No."].notna() & (df["Addr. No."].fillna("") != "")) | (df["BP Country"].fillna("") != "")
    street_cols = ["Street", "Street 2", "Street 3", "Street 4", "Street 5"]
    street2_or_street3_non_empty = (df["Street 2"].fillna("") != "") | (df["Street 3"].fillna("") != "")

    df["street_present_cols"] = df[street_cols].apply(
        lambda r: "|".join([c for c in street_cols if str(r[c]).strip() != ""]), axis=1
    )

    df["Empty street 2 - 3?"] = "OK"
    df.loc[street2_or_street3_non_empty, "Empty street 2 - 3?"] = "Not empty"
    df.loc[~has_address, "Empty street 2 - 3?"] = "No address found"

    # Builds diagnostics for language based on the address country
    is_fr_country = df["BP Country"].fillna("").isin(FRANCOPHONE_COUNTRIES)
    is_lang_fr = df["Language"].fillna("") == "F"
    is_lang_en = df["Language"].fillna("") == "E"
    is_lang_empty = df["Language"].fillna("") == ""

    df["Language diag"] = "OK"
    df.loc[is_fr_country & (~is_lang_fr), "Language diag"] = "Wrong language"
    df.loc[~is_fr_country & ~is_lang_en, "Language diag"] = "Wrong language"
    df.loc[is_lang_empty, "Language diag"] = "Empty language"
    df.loc[~has_address, "Language diag"] = "No address found"

    # Filters the columns for output
    result = df[
        [
            "BP",
            "Name",
            "Last Name",
            "First Name",
            "Created By",
            "Created On",
            "Addr. No.",
            "BP Country",
            "Language",
            "Street",
            "Street 2",
            "Street 3",
            "Street 4",
            "Street 5",
            "Empty street 2 - 3?",
            "Language diag",
        ]
    ].copy()

    # Applies lingua-based language detection for Belgian BPs
    be_mask = result["BP Country"] == "BE"
    if be_mask.any():
        result.loc[be_mask, "Language diag"] = result[be_mask].apply(diag_BE, axis=1).values

    print(f"[INFO] init BP={len(but000)}")
    print(f"[INFO] no_address={(result['Empty street 2 - 3?']=='No address found').sum()}")
    print(f"[INFO] wrong_language={(result['Language diag']=='Wrong language').sum()}")
    return result
    

def main() -> None:
    app_logger = Logger(mail=True, subject="Address-Language", path=__file__)
    _debug, log, _warn, error = log_helpers(app_logger)
    log("Start language and street check")
    try:
        df = build_diagnostic_df()
        # Dossier par execution pour historiser les controles.
        ts = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = OUTPUT_ROOT / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        out_xlsx = run_dir / "language_street_full.xlsx"
        street_issues_xlsx = run_dir / "street_issues.xlsx"
        language_issues_xlsx = run_dir / "language_issues.xlsx"

        # Filters the dataframe xith the issues based on the diag columns
        df.to_excel(out_xlsx, index=False)
        street_issues = df[df["Empty street 2 - 3?"] != "OK"].copy()
        language_issues = df[df["Language diag"] != "OK"].copy()
        street_issues.to_excel(street_issues_xlsx, index=False)
        language_issues.to_excel(language_issues_xlsx, index=False)

        log(f"Saved full XLSX: {out_xlsx}")
        log(f"Saved street issues XLSX: {street_issues_xlsx} ({len(street_issues)} rows)")
        log(f"Saved language issues XLSX: {language_issues_xlsx} ({len(language_issues)} rows)")

        # Sends mails
        if not street_issues.empty:
            send_quality_check_mail(
                subject=SUBJECT_STREET,
                body=STREET_CHANGE_TEMPLATE,
                file_path=street_issues_xlsx,
                logger=app_logger,
            )
            log("Street issues email sent")
        else:
            log("No street issue email sent (no issues)")
            send_quality_check_mail(
                subject=SUBJECT_STREET,
                body=NO_ISSUES_STREET_TEMPLATE,
                logger=app_logger,
            )

        if not language_issues.empty:
            send_quality_check_mail(
                subject=SUBJECT_LANGUAGE,
                body=LANGUAGE_CHANGE_TEMPLATE,
                file_path=language_issues_xlsx,
                logger=app_logger,
            )
            log("Language issues email sent")
        else:
            log("No language issue email sent (no issues)")
            send_quality_check_mail(
                subject=SUBJECT_LANGUAGE,
                body=NO_ISSUES_LANGUAGE_TEMPLATE,
                logger=app_logger,
            )
            
    except Exception:
        error("Failure during language and street check", exc_info=True)
        raise


if __name__ == "__main__":
    # debug_adrc_columns_for_address(DEBUG_ADRC_ADDRESS)
    main()

