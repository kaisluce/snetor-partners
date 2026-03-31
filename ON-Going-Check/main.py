from importBUT00 import load_but00
from Import_onGoingScreen import load_ongoing_screen
from importB1data import load_partner_changes
from latest_report import load_latest_report
from logger import logger as app_logger, log_helpers
from mails import send_quality_check_mail

import pandas as pd
import json
from datetime import date, timedelta
from pathlib import Path


# thefuzz est optionnel : si installé, on utilise la similarité floue pour matcher les noms.
# Sans lui, on tombe sur un matching exact (sous-chaîne).
try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

# Noms de BP à exclure car ce sont des entrées techniques/fictives dans SAP.
UNWANTED_NAMES = [
    "#DO NOT USE",
    "DO NOT USE",
    "#DEFAULT",
    "#DO NOT USE I.C.S.A"
]

# Entités internes du groupe SNETOR : on les exclut du contrôle On-Going Screen
# car elles ne sont pas des partenaires tiers à vérifier.
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

# Codes de groupe SAP (champ "Group" du BUT000) à inclure dans le contrôle.
# Ces groupes correspondent aux partenaires tiers actifs (clients, fournisseurs, etc.).
# Les autres groupes (ex : employés, divisions internes) sont ignorés.
GROUPS = [
    "ZG01",  # Clients
    "ZG02",  # Fournisseurs matières
    "ZG03",
    "ZG04",
    "ZG05",
    "ZG06",
    "ZG07",
    "ZG09",  # Fournisseurs frais généraux
    "ZG13",  # Clients livre (ship-to)
]

# Score minimum (sur 100) pour qu'un match fuzzy entre le nom du BP et un cas
# On-Going Screen soit considéré comme valide. Valeur déterminée empiriquement.
FUZZY_SCORE_THRESHOLD = 90

TODAY_DT = pd.Timestamp.today().normalize()
# Un cas On-Going Screen est considéré valide seulement s'il a été créé dans les 3 dernières années.
THREE_YEARS_AGO = TODAY_DT - pd.DateOffset(years=3)

# Répertoire racine des dossiers de compliance partenaires sur le serveur.
COMPLIANCE_PATH = Path(r"\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\1partner creation")

# Fichiers JSON persistant les cas et dossiers à ignorer lors des contrôles.
# JSON_PATHS[0] = cas On-Going Screen à ignorer (par BP)
# JSON_PATHS[1] = dossiers de compliance à ignorer (par BP)
JSON_PATHS = [
    r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\DO_NOT_DELETE\ignore_cases.json",
    r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN\DO_NOT_DELETE\ignore_folders.json"
]

# Les 4 dossiers de compliance correspondent aux catégories de partenaires :
# FOLDERS[0] = Clients (ZG01, CL...)
# FOLDERS[1] = Fournisseurs matières (ZG02-ZG07, FB/FT/FA)
# FOLDERS[2] = Fournisseurs frais généraux (ZG09)
# FOLDERS[3] = Clients livre / Ship-to (ZG13, CL fallback)
FOLDERS = [
    COMPLIANCE_PATH / "001 Clients - Customers",
    COMPLIANCE_PATH / "004 Fournisseurs - Suppliers",
    COMPLIANCE_PATH / "005 Fournisseurs Frais Generaux - General Expense Suppliers",
    COMPLIANCE_PATH / "002 Clients livre - Ship to Customers"
]

# Pré-charge la liste des sous-dossiers pour chaque dossier de compliance existant.
# Évite de relire le disque à chaque ligne traitée.
COMPLIANCE_NAMES = {
    folder: [d.name for d in folder.iterdir() if d.is_dir()]
    for folder in FOLDERS
    if folder.exists()
}

BASE_SAVE_PATH = Path(r"\\snetor-docs\Users\MDM\998_CHecks\Bp-ON_GOING_SCREEN")
SUBJECT = "On Going Screen"

# Corps des mails selon qu'il y ait ou non des anomalies détectées.
CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires dont la compliance est manquante."
)

NO_CHANGE_TEMPLATE = (
    "Toutes les donnees On Going Screen sont conformes."
)


def _as_bool(value) -> bool:
    """Convertit une valeur quelconque en booléen.
    Accepte les strings "1", "true", "yes", "y", "vrai" (insensible à la casse).
    Retourne False si la valeur est None ou non reconnue.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "vrai"}


def _normalize_str_list(value) -> list[str]:
    """Normalise une valeur en liste de chaînes uniques et non vides.
    Accepte une string CSV ("a,b,c") ou une liste Python.
    Déduplique en ignorant la casse, tout en préservant la casse originale.
    """
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
    """Extrait le numéro de BP depuis une ligne, en nettoyant les espaces.
    Note : les deux appels row.get("Bp") sont identiques — le second était
    prévu pour une variante de colonne mais n'a pas encore été implémenté.
    """
    return str(row.get("Bp") or row.get("Bp") or "").strip()


def _get_bp_column(df: pd.DataFrame | None) -> str | None:
    """Retourne le nom de la colonne BP dans le DataFrame, ou None si absent.
    Actuellement, seul "Bp" est supporté. La deuxième vérification est redondante
    (copier-coller) et pourrait être étendue à d'autres variantes ("BP", "bp"...).
    """
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
        # Charge les mouvements de partenaires B1 sur les 2 dernières semaines.
        b1_changes = load_partner_changes(date.today() - timedelta(weeks=2), TODAY_DT.date(), logger=log)
        b1_changes = b1_changes.rename(columns={"Nom Partenaire": "Name"})
        # Exclut les partenaires dont le code commence par FG (frais généraux internes)
        # ou FS (fournisseurs de services internes) — non soumis au contrôle On-Going.
        b1_changes = b1_changes[~b1_changes["Code Partenaire"].str[:2].isin(["FG", "FS"])]
        _log(f"B1 partner changes loaded: {len(b1_changes)} rows")

        but00 = load_but00(logger=log)
        ongoing = load_ongoing_screen(logger=log)

        # Reconstruit un nom unique en concaténant les 4 champs de nom SAP (Name 1 à 4),
        # puis normalise les espaces multiples.
        but00["Name"] = (
            but00[["Name 1", "Name 2", "Name 3", "Name 4"]]
            .fillna("")
            .astype(str)
            .agg(" ".join, axis=1)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        but00 = but00.drop(columns=["Name 1", "Name 2", "Name 3", "Name 4"])

        # Filtre les BP sans nom significatif (moins de 3 caractères),
        # les noms techniques/fictifs, les entités internes SNETOR,
        # et les divisions marquées comme inutilisables.
        but00 = but00[but00["Name"].fillna("").str.strip().str.len() > 2]
        but00 = but00[~but00["Name"].isin(UNWANTED_NAMES)]
        but00 = but00[~but00["Name"].isin(SNETOR_ENTITIES)]
        but00 = but00[~but00["Name"].fillna("").str.contains("# DIVISION NE PAS UTILISER", regex=False)]

        # Ne garde que les groupes SAP concernés par le contrôle On-Going Screen.
        but00 = but00[but00["Group"].isin(GROUPS)]

        # Remplace les espaces insécables (U+00A0) par des espaces normaux
        # et normalise les espaces multiples — problème fréquent dans les exports SAP.
        but00["Name"] = (
            but00["Name"]
            .fillna("")
            .str.replace("\u00A0", " ", regex=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

        # Trie par date de création décroissante pour que les BP les plus récents
        # soient traités en premier dans les rapports.
        but00 = but00.sort_values(by=["Creation date"], ascending=False).reset_index(drop=True)
        _debug(f"Filtered BUT000 rows: {len(but00)}")

        # Charge le dernier rapport généré (pour réutiliser les décisions manuelles précédentes).
        try:
            report = load_latest_report()
            _log("Latest report loaded")
        except Exception as exc:
            _error(f"Error loading latest report: {exc}", exc_info=True)
            report = None

        # Charge les listes de cas et dossiers à ignorer (corrections manuelles persistées en JSON).
        try:
            ignore_cases, ignore_folders = import_jsons()
            _log("JSONs loaded")
        except Exception as exc:
            _error(f"Error loading JSONs: {exc}", exc_info=True)
            ignore_cases = {}
            ignore_folders = {}

        # Crée un sous-dossier horodaté pour historiser chaque exécution du contrôle.
        ts = pd.Timestamp.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = BASE_SAVE_PATH / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        # --- Contrôle On-Going Screen S4 (SAP) ---
        _log("Checking on going screen for S4...")
        results = but00.apply(treat_line_partner, axis=1, ignore_cases=ignore_cases, previous = report, ongoing=ongoing, logger=log)
        results.to_excel(run_dir / "results.xlsx")

        # --- Contrôle des dossiers de compliance S4 ---
        _log("Checking compliance folders for S4...")
        with_folder = results.apply(look_for_folder, ignore_folders=ignore_folders, previous = report, axis=1, logger=log)
        with_folder.to_excel(run_dir / "results_with_folder.xlsx")

        # --- Contrôle On-Going Screen B1 (Business One) ---
        _log("Checking on going screens for B1...")
        results_B1 = b1_changes.apply(treat_line_partner, ignore_cases=ignore_cases, axis=1, previous = report, ongoing=ongoing, logger=log)
        results_B1.to_excel(run_dir / "results_B1.xlsx")

        # --- Contrôle des dossiers de compliance B1 ---
        _log("Checking compliance folders for B1...")
        with_folder_B1 = results_B1.apply(look_for_folder, ignore_folders=ignore_folders, previous = report, axis=1, logger=log)
        with_folder_B1.to_excel(run_dir / "results_B1_with_folder.xlsx")

        # Harmonise le nom de colonne BP entre S4 ("Bp") et B1 ("Code Partenaire")
        # pour pouvoir concaténer les deux DataFrames.
        with_folder_B1.rename(columns={"Code Partenaire": "Bp"}, inplace=True)

        # Colonnes attendues dans le résultat B1 — on les crée vides si absentes
        # pour garantir la cohérence lors du concat avec le résultat S4.
        with_folder_b1_output_cols = [
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
        ]

        for col in with_folder_b1_output_cols:
            if col not in with_folder_B1.columns:
                with_folder_B1[col] = ""

        with_folder_B1 = with_folder_B1[with_folder_b1_output_cols]

        # Fusionne les résultats S4 et B1 dans un seul DataFrame de conformité.
        compliance_checked = pd.concat([with_folder, with_folder_B1])

        # Réordonne les colonnes selon le format attendu dans le rapport final.
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

        # Identifie les BP avec au moins une anomalie de compliance :
        # dossier manquant, écran absent, écrans multiples ou date trop ancienne.
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

        # Envoie le mail de résultat avec ou sans pièce jointe selon les anomalies trouvées.
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
    """Vérifie si un partenaire (ligne SAP ou B1) possède un cas On-Going Screen valide.

    Logique :
    1. Récupère la liste des cas à ignorer depuis le JSON et le rapport précédent.
    2. Recherche dans l'écran On-Going un cas dont le nom correspond au BP
       (matching fuzzy si thefuzz est installé, sous-chaîne sinon).
    3. Remplit les colonnes "Missing Screen", "Multiple Screens", "valid creation date".
    """
    _debug, _log, _warn, _error = log_helpers(logger)
    ignore_case_names = []
    try:
        bp = _get_bp(row)
        bp_col = _get_bp_column(previous)
        # Cherche la ligne correspondant à ce BP dans le rapport précédent.
        if bp_col is None:
            previous_row = pd.Series(dtype=str)
        else:
            previous_row = previous[previous[bp_col] == bp]
            if previous_row.empty:
                previous_row = pd.Series(dtype=str)
            else:
                previous_row = previous_row.iloc[0]

        # Récupère les cas à ignorer depuis le JSON persisté (corrections manuelles).
        json_ignore = [] if ignore_cases is None else ignore_cases.get(bp, [])
        ignore_case_names = _normalize_str_list(json_ignore)

        # Si le rapport précédent signalait un mauvais match On-Going Screen pour ce BP,
        # on ajoute automatiquement ce cas à la liste d'ignorés pour éviter de le re-signaler.
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
        # Compare le nom du BP (en majuscules) aux noms des cas On-Going Screen.
        name = str(row.get("Name", "")).strip().upper()
        if not name:
            row["Multiple Screens"] = False
            row["Missing Screen"] = True
            return row

        case_names = ongoing["Case name"].fillna("").astype(str)
        if fuzz is None:
            # Sans thefuzz : matching simple — le nom du cas doit être une sous-chaîne du nom BP.
            compliance = ongoing[case_names.apply(lambda case_name: bool(case_name.strip()) and case_name in name)]
        else:
            # Avec thefuzz : score de similarité token_set_ratio (robuste aux mots dans le désordre).
            scores = case_names.apply(lambda x: fuzz.token_set_ratio(name, x))
            compliance = ongoing[scores >= FUZZY_SCORE_THRESHOLD]

        if not compliance.empty:
            # Retire les cas figurant dans la liste d'ignorés (corrections manuelles).
            ignore_set = {n.casefold() for n in ignore_case_names}
            compliance = compliance[
                ~compliance["Case name"].fillna("").astype(str).str.strip().str.casefold().isin(ignore_set)
            ]

            if len(compliance) > 1:
                # Plusieurs cas trouvés : on prend le premier (ordre du DataFrame OnGoing Screen)
                # et on signale qu'il y a plusieurs écrans pour ce BP.
                latest = compliance.iloc[0]
                row["Case Name"] = latest["Case name"]
                latest_date = latest["Case created date"]
                latest_date_dt = pd.to_datetime(latest_date, errors="coerce")
                multiple_compliance = False
                if len(compliance) > 1:
                    multiple_compliance = True
                row["Multiple Screens"] = multiple_compliance
                row["Case created date"] = latest_date
                # Le cas est considéré valide seulement s'il date de moins de 3 ans.
                row["valid creation date"] = pd.notna(latest_date_dt) and latest_date_dt >= THREE_YEARS_AGO
                row["Missing Screen"] = False

            else:
                # Un seul cas trouvé mais il correspond à un ignoré : considéré comme manquant.
                row["Multiple Screens"] = False
                row["Case created date"] = ""
                row["Missing Screen"] = True
            row["Names To Ignore"] = ",".join(ignore_case_names)
            row["Wrong On Going Check"] = ""
            return row
        else:
            # Aucun cas trouvé dans l'écran On-Going pour ce BP.
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
    """Retourne le nom à rechercher dans les dossiers de compliance.
    Priorité : Case Name (nom du cas On-Going Screen) > Name (nom SAP du BP).
    """
    return str(row.get("Case Name") or row.get("Name") or "").strip()


def find_folder(path: Path, name: str, names_to_ignore: list[str] = [], logger=None) -> Path | None:
    """Cherche un sous-dossier dans `path` dont le nom correspond à `name`.
    Utilise le matching fuzzy (token_set_ratio) si thefuzz est disponible,
    sinon un matching exact par sous-chaîne (insensible à la casse).
    Retourne le chemin du dossier trouvé, ou None si aucun match.
    Les dossiers listés dans `names_to_ignore` sont exclus du résultat.
    """
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
    """Vérifie si un dossier de compliance existe pour ce partenaire.

    Logique :
    1. Détermine le dossier cible selon le groupe SAP (ZG01, ZG02...) ou le préfixe
       du code partenaire B1 (CL, FB, FT, FA).
    2. Recherche un sous-dossier correspondant au nom du BP dans ce dossier.
    3. Remplit les colonnes "Has compliance folder" et "Compliance folder".
    """
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
                # Si le rapport précédent signalait un mauvais dossier pour ce BP,
                # on l'ajoute à la liste d'ignorés pour éviter de le re-signaler.
                if _as_bool(previous_row.get("Wrong compliance folder")):
                    prev_folder = str(previous_row.get("Compliance folder", "") or "").strip()
                    if prev_folder and prev_folder.casefold() not in {n.casefold() for n in ignore_case_names}:
                        ignore_case_names.append(prev_folder)

        # Persiste la liste mise à jour seulement si elle a changé.
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
            # Routing par groupe SAP vers le bon dossier de compliance.
            # ZG01 (Clients) : cherche d'abord dans Clients, puis Fournisseurs si non trouvé
            #   (un client peut aussi être référencé côté fournisseur).
            # ZG02-ZG07 (Fournisseurs matières) : uniquement dans Fournisseurs.
            # ZG09 (Frais généraux) : uniquement dans Fournisseurs Frais Généraux.
            # ZG13 (Clients livre/Ship-to) : uniquement dans Clients livre.
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
            # Pas de groupe SAP : partenaire B1. Routing par préfixe du code partenaire.
            # CL = Client B1 : cherche dans Clients, puis Clients livre en fallback.
            # FB/FT/FA = Fournisseur B1 : cherche dans Fournisseurs.
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
    """Charge les deux fichiers JSON de configuration des ignorés.
    Retourne deux dicts :
    - ignore_cases  : {bp: [case_names_to_ignore]}
    - ignore_folders: {bp: [folder_names_to_ignore]}
    Retourne des dicts vides si les fichiers sont absents ou invalides.
    """
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
    """Persiste une entrée {key: value} dans le fichier JSON à `path`.
    Crée le fichier s'il n'existe pas. Met à jour la clé si elle existe déjà.
    Le JSON est écrit avec indentation pour rester lisible manuellement.
    """
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
