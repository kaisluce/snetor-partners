from importBUT00 import load_but00
from Import_onGoingScreen import load_ongoing_screen
from importB1data import load_partner_changes
from latest_report import load_latest_report
from logger import logger as app_logger, log_helpers
from mails import send_quality_check_mail

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from datetime import date


try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

UNWANTED_NAMES = [
    "#DO NOT USE",
    "DO NOT USE",
    "#DEFAULT",
    "#DO NOT USE I.C.S.A"
]

SNETOR_ENTITIES = [
    "SNETOR",
    "SNETOR OVERSEAS",
    "SNETOR OVERSEAS SAS,"
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
    "SNETOR LOGISTICS"
    ]

GROUPS = [
    "ZG01",
    "ZG02",
    "ZG03",
    "ZG04",
    "ZG05",
    "ZG06",
    "ZG07",
    "ZG09",
    "ZG13",
]

FUZZY_SCORE_THRESHOLD = 90

TODAY_DT = pd.Timestamp.today().normalize()
THREE_YEARS_AGO = TODAY_DT - pd.DateOffset(years=3)

COMPLIANCE_PATH = Path(r"\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\1partner creation")

JSON_PATHS = [
    r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\DO_NOT_DELETE\ignore_cases.json",
    r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\DO_NOT_DELETE\ignore_folders.json"
]

FOLDERS = [
    COMPLIANCE_PATH / "001 Clients - Customers",
    COMPLIANCE_PATH / "004 Fournisseurs - Suppliers",
    COMPLIANCE_PATH / "005 Fournisseurs Frais Generaux - General Expense Suppliers",
    COMPLIANCE_PATH / "002 Clients livre - Ship to Customers"
]

COMPLIANCE_NAMES = {
    folder: [d.name for d in folder.iterdir() if d.is_dir()]
    for folder in FOLDERS
    if folder.exists()
}

BASE_SAVE_PATH = Path(r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN")
SUBJECT = "On Going Screen"

CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Vous trouverez en piece jointe le rapport listant les partenaires avec des anomalies On Going Screen.<br>"
    "Bonne journee."
)

NO_CHANGE_TEMPLATE = (
    "Bonjour,<br>"
    "Toutes les donnees On Going Screen sont conformes.<br>"
    "Bonne journee."
)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "vrai"}


def _normalize_str_list(value) -> list[str]:
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, list):
        items = value
    else:
        items = []

    out = []
    seen = set()
    for item in items:
        s = str(item).strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def _get_bp(row: pd.Series) -> str:
    return str(row.get("Bp") or row.get("Bp") or "").strip()


def _get_bp_column(df: pd.DataFrame | None) -> str | None:
    if df is None:
        return None
    if "Bp" in df.columns:
        return "Bp"
    if "Bp" in df.columns:
        return "Bp"
    return None

def main():
    log = app_logger(mail=True, subject=SUBJECT, path=__file__)
    _debug, _log, _warn, _error = log_helpers(log)
    try:
        b1_changes = load_partner_changes(date(2000, 1, 1), TODAY_DT.date(), logger=log)
        b1_changes = b1_changes.rename(columns={"Nom Partenaire": "Name"})
        b1_changes = b1_changes[~b1_changes["Code Partenaire"].str[:2].isin(["FG", "FS"])]
        b1_changes.to_excel(r"C:\Users\K.luce\OneDrive - SNETOR\Documents\partners\ON-Going-Check\b1_partner_changes.xlsx", index=False)
        _log(f"B1 partner changes loaded: {len(b1_changes)} rows")

        but00 = load_but00(logger=log)
        ongoing = load_ongoing_screen(logger=log)

        but00["Name"] = (
            but00[["Name 1", "Name 2", "Name 3", "Name 4"]]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        but00 = but00.drop(columns=["Name 1", "Name 2", "Name 3", "Name 4"])

        but00 = but00[but00["Name"].fillna("").str.strip().str.len() > 2]
        but00 = but00[~but00["Name"].isin(UNWANTED_NAMES)]
        but00 = but00[~but00["Name"].isin(SNETOR_ENTITIES)]
        but00 = but00[~but00["Name"].fillna("").str.contains("# DIVISION NE PAS UTILISER", regex=False)]

        but00 = but00[but00["Group"].isin(GROUPS)]

        but00["Name"] = (
            but00["Name"]
            .fillna("")
            .str.replace("\u00A0", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

        but00 = but00.sort_values(by=["Creation date"], ascending=False).reset_index(drop=True)
        _debug(f"Filtered BUT000 rows: {len(but00)}")
        
        try:
            report = load_latest_report()
            _log("Latest report loaded")
        except Exception as exc:
            _error(f"Error loading latest report: {exc}", exc_info=True)
            report = None
        
        try:
            ignore_cases, ignore_folders = import_jsons()
            _log("JSONs loaded")
        except Exception as exc:
            _error(f"Error loading JSONs: {exc}", exc_info=True)
            ignore_cases = {}
            ignore_folders = {}

        # Dossier par execution pour historiser les controles.
        ts = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = BASE_SAVE_PATH / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        _log("Checking on going screen for S4...")
        results = but00.apply(treat_line_partner, axis=1, ignore_cases=ignore_cases, previous = report, ongoing=ongoing, logger=log)
        results.to_excel(run_dir / "results.xlsx")

        _log("Checking compliance folders for S4...")
        with_folder = results.apply(look_for_folder, ignore_folders=ignore_folders, previous = report, axis=1, logger=log)
        with_folder.to_excel(run_dir / "results_with_folder.xlsx")

        _log("Checking on going screens for B1...")
        results_B1 = b1_changes.apply(treat_line_partner, ignore_cases=ignore_cases, axis=1, previous = report, ongoing=ongoing, logger=log)
        results_B1.to_excel(run_dir / "results_B1.xlsx")

        _log("Checking compliance folders for B1...")
        with_folder_B1 = results_B1.apply(look_for_folder, ignore_folders=ignore_folders, previous = report, axis=1, logger=log)
        with_folder_B1.to_excel(run_dir / "results_B1_with_folder.xlsx")

        with_folder_B1.rename(columns={"Code Partenaire": "Bp"}, inplace=True)
        with_folder_B1 = with_folder_B1[[
            "Bp",
            "Name",
            "Case Name",
            "Case created date",
            "Compliance folder",
            "Date Traitement",
            "Has compliance folder",
            "Missing Screen",
            "Multiple Screens",
            "Traitement",
            "Utilisateur",
            "source_database",
        ]]

        compliance_checked = pd.concat([with_folder, with_folder_B1])
        
        compliance_checked = compliance_checked.reindex(columns=[
            "Bp",
            "Name",
            "Creation date",
            "Decreator",
            "Group",
            "Traitement",
            "Date Traitement",
            "Utilisateur",
            "source_database",
            "Case Name",
            "Case created date",
            "Compliance folder",
            "Has compliance folder",
            "Missing Screen",
            "Multiple Screens",
            "valid creation date",
            "Wrong On Going Check",
            "Names To Ignore",
            "Wrong compliance folder",
            "Folder to Ignore",
        ])

        compliance_checked.to_excel(run_dir / "compliance_checked.xlsx")
        _log(f"Compliance checks exported to: {run_dir}")

        issue_filter = (
            (compliance_checked["Has compliance folder"] == False)
            | (compliance_checked["Missing Screen"] == True)
            | (compliance_checked["Multiple Screens"] == True)
            | (compliance_checked["valid creation date"] == False)
        )

        issue_on_compliance = compliance_checked[issue_filter]
        mail_attachment = None
        if not issue_on_compliance.empty:
            issue_file = run_dir / "issue_on_compliance.xlsx"
            issue_on_compliance.to_excel(issue_file)
            mail_attachment = str(issue_file)

        try:
            _log("Sending final email...")
            send_quality_check_mail(
                subject=SUBJECT,
                body=CHANGE_TEMPLATE if mail_attachment else NO_CHANGE_TEMPLATE,
                file_path=mail_attachment,
                logger=log,
            )
            _log("Final email sent.")
        except Exception as exc:
            _error(f"Final email failed: {exc}", exc_info=True)

        return
    except Exception as exc:
        _error(f"Unhandled error in main: {exc}", exc_info=True)
        raise


def treat_line_partner(row: pd.Series, ongoing: pd.DataFrame, ignore_cases: dict | None, previous: pd.DataFrame = None, logger=None):
    _debug, _log, _warn, _error = log_helpers(logger)
    ignore_case_names = []
    try:
        bp = _get_bp(row)
        bp_col = _get_bp_column(previous)
        if bp_col is None:
            previous_row = pd.Series(dtype=str)
        else:
            previous_row = previous[previous[bp_col] == bp]
            if previous_row.empty:
                previous_row = pd.Series(dtype=str)
            else:
                previous_row = previous_row.iloc[0]

        json_ignore = [] if ignore_cases is None else ignore_cases.get(bp, [])
        ignore_case_names = _normalize_str_list(json_ignore)

        if _as_bool(previous_row.get("Wrong On Going Check")):
            case_name = str(previous_row.get("Case Name", "") or "").strip()
            if case_name and case_name.casefold() not in {n.casefold() for n in ignore_case_names}:
                ignore_case_names.append(case_name)
            save_json_line(bp, ignore_case_names, JSON_PATHS[0])

        row["Names To Ignore"] = ",".join(ignore_case_names)
        row["Wrong On Going Check"] = ""
    except Exception as e:
        _warn(f"Error while fetching previous cases to ignore: {e}")
        row["Names To Ignore"] = ",".join(ignore_case_names)
        row["Wrong On Going Check"] = ""
    
    try:
        name = str(row.get("Name", "")).strip().upper()
        if not name:
            row["Multiple Screens"] = False
            row["Missing Screen"] = True
            return row

        case_names = ongoing["Case name"].fillna("").astype(str)
        if fuzz is None:
            compliance = ongoing[case_names.apply(lambda case_name: bool(case_name.strip()) and case_name in name)]
        else:
            scores = case_names.apply(lambda x: fuzz.token_set_ratio(name, x))
            compliance = ongoing[scores >= FUZZY_SCORE_THRESHOLD]

        if not compliance.empty:
            
            ignore_set = {n.casefold() for n in ignore_case_names}
            compliance = compliance[
                ~compliance["Case name"].fillna("").astype(str).str.strip().str.casefold().isin(ignore_set)
            ]
            
            if len(compliance) > 1:
                
                latest = compliance.iloc[0]
                row["Case Name"] = latest["Case name"]
                latest_date = latest["Case created date"]
                latest_date_dt = pd.to_datetime(latest_date, errors="coerce")
                multiple_compliance = False
                if len(compliance) > 1:
                    multiple_compliance = True
                row["Multiple Screens"] = multiple_compliance
                row["Case created date"] = latest_date
                row["valid creation date"] = pd.notna(latest_date_dt) and latest_date_dt >= THREE_YEARS_AGO
                row["Missing Screen"] = False
            
            else:
                row["Multiple Screens"] = False
                row["Case created date"] = ""
                row["Missing Screen"] = True
            row["Names To Ignore"] = ",".join(ignore_case_names)
            row["Wrong On Going Check"] = ""
            return row
        else:
            row["Multiple Screens"] = False
            row["Case created date"] = ""
            row["Missing Screen"] = True
        return row
    except Exception as exc:
        _error(f"Error in treat_line_partner for Bp={row.get('Bp', '')} Name={row.get('Name', '')}: {exc}", exc_info=True)
        row["Multiple Screens"] = False
        row["Case created date"] = ""
        row["Missing Screen"] = True
        return row

def get_name_to_search(row: pd.Series) -> str:
    return str(row.get("Case Name") or row.get("Name") or "").strip()


def find_folder(path: Path, name: str, names_to_ignore: list[str] = [], logger=None) -> Path | None:
    _debug, _log, _warn, _error = log_helpers(logger)
    try:
        names = COMPLIANCE_NAMES.get(path, [])
        for n in names:
            if fuzz is None:
                if name and n and name.upper() in n.upper():
                    return path / n
            else:
                if fuzz.token_set_ratio(name.upper(), n.upper()) >= FUZZY_SCORE_THRESHOLD and n.casefold() not in {name.casefold() for name in names_to_ignore}:
                    return path / n
        return None
    except Exception as exc:
        _error(f"Error in find_folder for path={path}, name={name}: {exc}", exc_info=True)
        return None


def look_for_folder(row: pd.Series, ignore_folders: dict | None = None, previous: pd.DataFrame = None, logger=None):
    _debug, _log, _warn, _error = log_helpers(logger)
    ignore_case_names = []
    try:
        bp = _get_bp(row)
        raw_ignore = [] if ignore_folders is None else ignore_folders.get(bp, [])
        ignore_case_names = _normalize_str_list(raw_ignore)
        before_len = len(ignore_case_names)

        # Keep the last wrong fuzzy match from previous report in the ignore list.
        bp_col = _get_bp_column(previous)
        if bp_col is not None:
            previous_row = previous[previous[bp_col] == bp]
            if not previous_row.empty:
                previous_row = previous_row.iloc[0]
                if _as_bool(previous_row.get("Wrong compliance folder")):
                    prev_folder = str(previous_row.get("Compliance folder", "") or "").strip()
                    if prev_folder and prev_folder.casefold() not in {n.casefold() for n in ignore_case_names}:
                        ignore_case_names.append(prev_folder)

        if len(ignore_case_names) != before_len:
            save_json_line(bp, ignore_case_names, JSON_PATHS[1])

        row["Folder to Ignore"] = ",".join(ignore_case_names)
        row["Wrong compliance folder"] = ""
    except Exception as exc:
        _warn(f"Error while fetching folders to ignore from JSON/previous report: {exc}")
        row["Folder to Ignore"] = ",".join(ignore_case_names)
        row["Wrong compliance folder"] = ""
    
    try:
        group = str(row.get("Group", "")).strip()
        name = get_name_to_search(row)
        found = None

        if group:
            match group:
                case "ZG01":
                    found = find_folder(FOLDERS[0], name, names_to_ignore=ignore_case_names, logger=logger)
                    if found is None:
                        found = find_folder(FOLDERS[1], name, names_to_ignore=ignore_case_names, logger=logger)
                case "ZG02" | "ZG03" | "ZG04" | "ZG05" | "ZG06" | "ZG07":
                    found = find_folder(FOLDERS[1], name, names_to_ignore=ignore_case_names, logger=logger)
                case "ZG09":
                    found = find_folder(FOLDERS[2], name, names_to_ignore=ignore_case_names, logger=logger)
                case "ZG13":
                    found = find_folder(FOLDERS[3], name, names_to_ignore=ignore_case_names, logger=logger)
            if not found is None:
                row["Compliance folder"] = found
                row["Has compliance folder"] = True
            else:
                row["Has compliance folder"] = False
            return row
        else:
            code = str(row.get("Code Partenaire", "")).strip()
            match code[:2]:
                case "CL":
                    found = find_folder(FOLDERS[0], name, names_to_ignore=ignore_case_names, logger=logger)
                    if found is None:
                        found = find_folder(FOLDERS[3], name, names_to_ignore=ignore_case_names, logger=logger)
                case "FB" | "FT" | "FA":
                    found = find_folder(FOLDERS[1], name, names_to_ignore=ignore_case_names, logger=logger)
            if not found is None:
                row["Compliance folder"] = found
                row["Has compliance folder"] = True
            else:
                row["Has compliance folder"] = False
            return row
    except Exception as exc:
        _error(f"Error in look_for_folder for Bp={row.get('Bp', '')} Name={row.get('Name', '')}: {exc}", exc_info=True)
        row["Has compliance folder"] = False
        if "Compliance folder" not in row:
            row["Compliance folder"] = ""
        return row
    
def import_jsons():
    ignore_cases = {}
    ignore_folders = {}

    try:
        with open(JSON_PATHS[0], "r", encoding="utf-8-sig") as f:
            raw = f.read().strip()
            if raw:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    ignore_cases = loaded
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        ignore_cases = {}

    try:
        with open(JSON_PATHS[1], "r", encoding="utf-8-sig") as f:
            raw = f.read().strip()
            if raw:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    ignore_folders = loaded
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        ignore_folders = {}

    return ignore_cases, ignore_folders

def save_json_line(key, value, path):
    json_path = Path(path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if json_path.exists() and json_path.stat().st_size > 0:
        with open(json_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded

    data[str(key)] = value

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data
        


if __name__ == "__main__":
    main()
