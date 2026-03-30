"""Controle langue vs pays et champs rue pour les BP.

Entrees: BP_BUT000.csv, BP_BUT020.csv, BP_ADRC.csv.
Sorties: dossier horodate sous OUTPUT_ROOT + rapports XLSX + emails si anomalies.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime


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
    "Vous trouverez en piece jointe la liste des BPs dont la street 2 ou 3 ne sont pas à vides."
)
LANGUAGE_CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport des BPs avec les mauvaises Langues."
)
NO_ISSUES_STREET_TEMPLATE = (
    "Tous les champs street 2 ou street3 sont à vide."
)
NO_ISSUES_LANGUAGE_TEMPLATE = (
    "Toutes les langues sont conformes."
)

# Diagnostic values
DIAG_OK                  = "OK"
DIAG_WRONG_LANGUAGE      = "Wrong Language"
DIAG_EMPTY_LANGUAGE      = "Empty language"
DIAG_NO_ADDRESS          = "No address found"
DIAG_NOT_EMPTY           = "Not empty"
DIAG_NO_STREET           = "No street found for BE diag"
DIAG_NO_LANG_DETECTED    = "No language detected with street"

# Column names
BP                    = "BP"
NAME                  = "Name"
LAST_NAME             = "Last Name"
FIRST_NAME            = "First Name"
CREATED_ON            = "Created On"
CREATED_BY            = "Created By"
CORR_LANG             = "Correspondence Language"
ADDR_NO               = "Addr. No."
BP_COUNTRY            = "BP Country"
LANGUAGE              = "Language"
STREET                = "Street"
STREET_2              = "Street 2"
STREET_3              = "Street 3"
STREET_4              = "Street 4"
STREET_5              = "Street 5"
STREET_PRESENT_COLS   = "street_present_cols"
EMPTY_STREET_DIAG     = "Empty street 2 - 3?"
LANGUAGE_DIAG         = "Language diag"
EXPECTED_LANGUAGE     = "Expected language"

REPORT_NAME = "language_street_full.xlsx"


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
    .from_all_languages()
    .build()
)

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
    df.columns = [BP, NAME, LAST_NAME, FIRST_NAME, CREATED_ON, CREATED_BY, CORR_LANG]
    df[BP] = _normalize_bp(df[BP])
    df[NAME] = df[NAME].fillna("").astype(str).str.strip()
    df[LAST_NAME] = df[LAST_NAME].fillna("").astype(str).str.strip()
    df[FIRST_NAME] = df[FIRST_NAME].fillna("").astype(str).str.strip()
    df[CREATED_ON] = df[CREATED_ON].fillna("").astype(str).str.strip()
    df[CREATED_BY] = df[CREATED_BY].fillna("").astype(str).str.strip()

    init = len(df)
    df = df[df[BP] != ""].reset_index(drop=True)
    df = df[~df[NAME].str.startswith("#", na=False)].reset_index(drop=True)
    df = df[~df[BP].str.startswith("9", na=False)].reset_index(drop=True)
    df = df[~df[BP].str.startswith("5", na=False)].reset_index(drop=True)
    df = df[~df[BP].str.startswith("29", na=False)].reset_index(drop=True)

    df = df[~df[BP].isin(["10000010", "10000012"])]

    personnes = (df[NAME] == "") & ~((df[LAST_NAME] == "") & (df[FIRST_NAME] == ""))
    personnes_diez = personnes & (df[LAST_NAME].str.contains("#", na=False) | df[FIRST_NAME].str.contains("#", na=False))
    df.loc[personnes, NAME] = "(person)" + (df.loc[personnes, LAST_NAME] + " " + df.loc[personnes, FIRST_NAME]).str.strip()
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
    df.columns = [BP, ADDR_NO]
    df[BP] = _normalize_bp(df[BP])
    df[ADDR_NO] = _normalize_addr(df[ADDR_NO])
    idx = df.groupby(BP)[ADDR_NO].idxmax()
    return df.loc[idx, [BP, ADDR_NO]].reset_index(drop=True)


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
    df.columns = [ADDR_NO, BP_COUNTRY, LANGUAGE, STREET, STREET_2, STREET_3, STREET_4, STREET_5]
    df[ADDR_NO] = _normalize_addr(df[ADDR_NO])
    df[BP_COUNTRY] = df[BP_COUNTRY].fillna("").astype(str).str.strip().str.upper()
    return df.reset_index(drop=True)
            

def diag_BE(row: pd.Series) -> str:
    streets_cols = [STREET, STREET_2, STREET_3, STREET_4, STREET_5]
    streets_list = [row.get(col) if str(row.get(col, "")).strip() != "" else None for col in streets_cols]
    streets_str = " ".join([str(s) for s in streets_list if s is not None])

    if not streets_str.strip():
        return DIAG_NO_STREET

    fr_confidence = _BE_DETECTOR.compute_language_confidence(streets_str, Language.FRENCH)
    if fr_confidence == 0.0:
        return DIAG_NO_LANG_DETECTED

    expected_language = "F" if fr_confidence >= 0.3 else "E"
    sap_lang = str(row.get(LANGUAGE, "")).strip().upper()

    if sap_lang == expected_language:
        return DIAG_OK
    return DIAG_WRONG_LANGUAGE
    

def main() -> None:
     
    def load_latest_report() -> pd.DataFrame:
        def get_all_dirs():
            dirs = [d for d in OUTPUT_ROOT.iterdir() if d.is_dir()]
            return dirs

        def get_latest_report_path(dirs):
            
            if not dirs:
                return None
            
            def _is_timestamped(d: Path) -> bool:
                try:
                    datetime.strptime(d.name, "%Y-%m-%d_%H-%M-%S")
                    return True
                except ValueError:
                    return False

            timestamped_dirs = [d for d in dirs if _is_timestamped(d)]
            while timestamped_dirs:
                latest_dir = max(timestamped_dirs, key=lambda x: x.name)

                report_path = latest_dir / REPORT_NAME
                if report_path.exists():
                    log(f"Found {REPORT_NAME} in {latest_dir}")
                    return report_path
                
                timestamped_dirs.remove(latest_dir)
            _warn(f"Couldn't find latest {REPORT_NAME} in {OUTPUT_ROOT}")
            return None
        
        report_directories = get_all_dirs()
        report_path = get_latest_report_path(report_directories)
        
        if report_path is None:
            return None
        latest_report =  pd.read_excel(report_path)
        while (
            latest_report.empty
            or not BP in latest_report.columns
            or not EXPECTED_LANGUAGE in latest_report.columns
               ):
            report_directories.remove(report_path.parent)
            if len(report_directories) == 0:
                return None
            report_path = get_latest_report_path(report_directories)
            if report_path is None:
                return None
            latest_report = pd.read_excel(report_path)
            
        result = latest_report[[BP, EXPECTED_LANGUAGE]].dropna(subset=[EXPECTED_LANGUAGE]).reset_index(drop=True)
        result[BP] = _normalize_bp(result[BP])
        return result



    def build_diagnostic_df() -> pd.DataFrame:
        """
        Merges all table together and builds the diagnostic dataframe
        """
        but000 = load_but000()
        but020 = load_but020()
        adrc = load_adrc()

        # Merges the tables with the partner informations and the address to analise the language
        addr = but020.merge(adrc, on=ADDR_NO, how="outer")
        df = but000.merge(addr, on=BP, how="left")

        # Fetches the Language from ADRC for people
        personnes = df[NAME].str.startswith("(person)", na=False)
        df.loc[personnes, LANGUAGE] = df.loc[personnes, CORR_LANG].fillna("").astype(str).str.strip().str.upper()
        df.drop(columns=[CORR_LANG], inplace=True)

        # Checks to see if the partners has any street 2 or 3
        has_address = (df[ADDR_NO].notna() & (df[ADDR_NO].fillna("") != "")) | (df[BP_COUNTRY].fillna("") != "")
        street_cols = [STREET, STREET_2, STREET_3, STREET_4, STREET_5]
        street2_or_street3_non_empty = (df[STREET_2].fillna("") != "") | (df[STREET_3].fillna("") != "")

        df[STREET_PRESENT_COLS] = df[street_cols].apply(
            lambda r: "|".join([c for c in street_cols if str(r[c]).strip() != ""]), axis=1
        )

        df[EMPTY_STREET_DIAG] = DIAG_OK
        df.loc[street2_or_street3_non_empty, EMPTY_STREET_DIAG] = DIAG_NOT_EMPTY
        df.loc[~has_address, EMPTY_STREET_DIAG] = DIAG_NO_ADDRESS

        # Builds diagnostics for language based on the address country
        is_fr_country = df[BP_COUNTRY].fillna("").isin(FRANCOPHONE_COUNTRIES)
        is_lang_fr = df[LANGUAGE].fillna("") == "F"
        is_lang_en = df[LANGUAGE].fillna("") == "E"
        is_lang_empty = df[LANGUAGE].fillna("") == ""

        df[LANGUAGE_DIAG] = DIAG_OK
        df.loc[is_fr_country & (~is_lang_fr), LANGUAGE_DIAG] = DIAG_WRONG_LANGUAGE
        df.loc[~is_fr_country & ~is_lang_en, LANGUAGE_DIAG] = DIAG_WRONG_LANGUAGE
        df.loc[is_lang_empty, LANGUAGE_DIAG] = DIAG_EMPTY_LANGUAGE
        df.loc[~has_address, LANGUAGE_DIAG] = DIAG_NO_ADDRESS

        # Applies lingua-based language detection for Belgian BPs
        be_mask = df[BP_COUNTRY] == "BE"
        if be_mask.any():
            df.loc[be_mask, LANGUAGE_DIAG] = df[be_mask].apply(diag_BE, axis=1).values

        df = override_language(df)
        
        # Filters the columns for output
        result = df[
            [
                BP, NAME, LAST_NAME, FIRST_NAME, CREATED_BY, CREATED_ON,
                ADDR_NO, BP_COUNTRY, LANGUAGE,
                STREET, STREET_2, STREET_3, STREET_4, STREET_5,
                EMPTY_STREET_DIAG, LANGUAGE_DIAG, EXPECTED_LANGUAGE,
            ]
        ].copy()
        
        print(f"[INFO] init BP={len(but000)}")
        print(f"[INFO] no_address={(result[EMPTY_STREET_DIAG]==DIAG_NO_ADDRESS).sum()}")
        print(f"[INFO] wrong_language={(result[LANGUAGE_DIAG]==DIAG_WRONG_LANGUAGE).sum()}")
        return result


    def override_language(df: pd.DataFrame):
        # Managing Languages overrides
        languages_overides = load_latest_report()
        if languages_overides is not None:
            df = df.merge(languages_overides, on=BP, how="left")
            overriden_languages = df[EXPECTED_LANGUAGE].notna()
            right_language = df[EXPECTED_LANGUAGE].str.strip() == df[LANGUAGE]
            df.loc[overriden_languages & ~right_language, LANGUAGE_DIAG] = DIAG_WRONG_LANGUAGE
            df.loc[overriden_languages & right_language, LANGUAGE_DIAG] = DIAG_OK
        else:
            df[EXPECTED_LANGUAGE] = None
        return df


    app_logger = Logger(mail=True, subject="Address-Language", path=__file__)
    _debug, log, _warn, error = log_helpers(app_logger)
    log("Start language and street check")
    try:
        df = build_diagnostic_df()
        # Dossier par execution pour historiser les controles.
        ts = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = OUTPUT_ROOT / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        out_xlsx = run_dir / REPORT_NAME
        street_issues_xlsx = run_dir / "street_issues.xlsx"
        language_issues_xlsx = run_dir / "language_issues.xlsx"

        # Filters the dataframe xith the issues based on the diag columns
        df.to_excel(out_xlsx, index=False)
        street_issues = df[df[EMPTY_STREET_DIAG] != DIAG_OK].copy()
        language_issues = df[df[LANGUAGE_DIAG] != DIAG_OK].copy()
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

