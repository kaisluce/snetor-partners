import asyncio
import pandas as pd
import csv
import re
from datetime import datetime
from typing import Optional
from pathlib import Path

from enrish_bp import enrish_bp
from mails import send_quality_check_mail

from logger import logger, log_helpers

BUT_000 = r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT000.csv"
BUT_020 = r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_BUT020.csv"
ADRC = r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_ADRC.csv"
CREDS = r"\\interfacessap.file.core.windows.net\interfacess4p\data_mdm_export\BP_TAXNUM.csv"
OUTPUT_DIR = r"\\snetor-docs\Users\MDM\998_CHecks\BP-ENRISHED_BP"

CHANGE_TEMPLATE = (
    "Vous trouverez en piece jointe le rapport listant les partenaires dont les informations ont ete completees."
)

NO_CHANGE_TEMPLATE = (
    "Aucun BP n'a ete corrige."
)
SUBJECT = "BP Enrichment"

def _normalize_identifier(value, digits_only: bool = True, pad_width: Optional[int] = None) -> str:
    """Normalize identifiers: strip, remove trailing .0, keep as string."""
    if pd.isna(value):
        return ""
    s = str(value).strip().strip('"').strip("'")
    s = re.sub(r"\.0+$", "", s)
    if digits_only:
        s = re.sub(r"\D+", "", s)
    if pad_width and s:
        s = s.zfill(pad_width)
    return s

def _normalize_bp_value(value: str) -> str:
    """
    Normalize BP identifiers by trimming spaces/quotes and left-padding to 10 digits
    when the value is numeric.
    """
    return _normalize_identifier(value, digits_only=True, pad_width=10)

def _normalize_addr_value(value: str) -> str:
    """Normalize address identifiers similarly to BP (keep digits, strip .0)."""
    return _normalize_identifier(value, digits_only=True, pad_width=None)

def _coerce_id_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Force identifier columns to string to avoid scientific notation and truncation."""
    id_columns = ("BP", "partner", "Business Partner", "siren", "siret", "Addr. No.")
    bp_columns = {"BP", "partner", "Business Partner"}
    for col in id_columns:
        if col in frame.columns:
            if col in bp_columns:
                frame[col] = frame[col].apply(_normalize_bp_value)
            elif col == "Addr. No.":
                frame[col] = frame[col].apply(_normalize_addr_value)
            else:
                frame[col] = frame[col].astype(str).str.strip().str.strip('"').str.strip()
    return frame


def build_data():
    
    def detect_skiprows(table) -> int:
        """Ignore une éventuelle ligne d'en-tête 'UNKNOWN TEXT' en début de fichier."""
        try:
            with open(table, "r", encoding="utf-8", errors="ignore") as f:
                first = f.readline().strip()
        except OSError:
            return 0
        return 1 if "UNKNOWN" in first.upper() else 0
        
    def set_missing(row: pd.Series):
        """Sets the missing values columns for each partner, making sure a bad entry counts as missing."""
        def _missing(value) -> bool:
            if pd.isna(value):
                return True
            if isinstance(value, str):
                return value.strip().lower() in {"", "none", "nan", "n/a"} and len(value.strip()) < 9
            return False

        def _missing_siren(value) -> bool:
            if pd.isna(value):
                return True
            if isinstance(value, str):
                if not value.strip().isdigit():
                    return True
                return value.strip().lower() in {"", "none", "nan", "n/a"} and len(value.strip()) != 9
            return False
        
        def _missing_siret(value) -> bool:
            if pd.isna(value):
                return True
            if isinstance(value, str):
                if not value.strip().isdigit():
                    return True
                return value.strip().lower() in {"", "none", "nan", "n/a"} and len(value.strip()) != 14 and not value.strip().isdigit()
            return False

        row["missing siren"] = _missing_siren(row.get("siren"))
        row["missing siret"] = _missing_siret(row.get("siret"))
        # La colonne issue du pivot est "VAT" (majuscule)
        vat_val = "VAT" if "VAT" in row else "vat"
        row["missing vat"] = _missing(row.get(vat_val))
        if row['missing siren']:
            row['siren'] = None
        if row['missing siret']:
            row['siret'] = None
        if row['missing vat']:
            row[vat_val] = None
        return row
        
    
    
    #Import the BUT 000 to get every partners
    datas_table = pd.read_csv(
        BUT_000,
        sep=";",
        engine="python",
        dtype=str,
        quoting=csv.QUOTE_NONE,
        on_bad_lines="skip",
        skiprows=1,
        header=None,
        names=[
            "Business Partner",
            "Grp.",
            "Arch. Flag",
            "Central",
            "AGrp",
            "Search Term 1",
            "Search Term 2",
            "Name 1",
            "Ext. No.",
            "CatP",
            "Name 2",
            "Last Name",
            "First Name",
            "Date",
            "User",
            "Name 3",
            "Name 4",
            "Date.1",
            "User.1",
        ]
    )
    datas_table = _coerce_id_columns(datas_table)   #Coerce BP to string
    
    log("Fetched BUT000")
    
    personnes = (datas_table["Name 1"] == "") & ~(
        (datas_table["Last Name"] == "") & (datas_table["First Name"] == "")
    )
    personnes_diez = personnes & (datas_table["Last Name"].str.contains("#", na=False) | datas_table["First Name"].str.contains("#", na=False))
    personnes_strt_diez = personnes_diez & datas_table["Last Name"].str.startswith("#", na=False)
    datas_table.loc[personnes, "Name 1"] = (
        datas_table.loc[personnes, "Last Name"] + " " + datas_table.loc[personnes, "First Name"]
    ).str.strip()
    datas_table.loc[~personnes_strt_diez & personnes_diez, "Name 1"] =  "# " + datas_table.loc[~personnes_strt_diez & personnes_diez, "Name 1"]

    
    #Import of the adresses for the BPs
    #Import the BUT 020, used as a link between partners and the addresses
    join_table = pd.read_csv(
        BUT_020,
        sep=";",
        engine="python",
        quoting=csv.QUOTE_NONE,
        on_bad_lines="skip",
        dtype=str,
        names=["Business Partner", "Addr. No.", "Not Used"],
    ).astype(str)
    join_table = _coerce_id_columns(join_table)
    join_table = join_table[["Business Partner", "Addr. No."]]
    debug(join_table.head())
    
    log("Fetched BUT020")
    
    #Import the ADRC, containing the addresses
    adress_table = pd.read_csv(
        ADRC,
        sep=";",
        engine="python",
        dtype=str,
        skiprows=detect_skiprows(ADRC),
        quoting=csv.QUOTE_NONE,
        on_bad_lines="skip",
        header=None,
    )
    adress_table = _coerce_id_columns(adress_table)
    
    log("Fetched ADRC")
    
    #Merge the three tables to have a complete adress table
    out = merge_address(datas_table, join_table, adress_table)
    
    log("Merged adress tables")
    
    #Import the credentials table, containing siren/siret/vat
    creds = pd.read_csv(
        CREDS,
        sep=";",
        header=None,
        skiprows=detect_skiprows(CREDS),
        dtype=str,
        usecols=[0, 1, 3],
        names=["BP", "value", "type"],
        on_bad_lines="skip",
        engine="python",
    )
    
    log("Fetched credentials")
    
    # Cleaning to use only french BPs and pivoting the credentials table
    creds["type"] = creds["type"].astype(str).str.strip().str.upper()
    creds["BP"] = creds["BP"].astype(str).str.strip()
    creds = creds[creds["type"].isin(["FR0", "FR1", "FR2"])]
    
    creds = (
        creds.pivot_table(
            index="BP",
            columns="type",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"FR0" : "VAT", "FR1": "siret", "FR2": "siren"})
    )
    creds = _coerce_id_columns(creds)   #Coerce vat/siren/siret to string
    
    log("Pivoted credentials")
    
    #Merge datas with creds
    merged = out.merge(creds, on="BP", how="left")
    
    # Filtering to keep only the used French BPs that need to be completed
    grp_series = merged["Grp."].astype(str)
    grouping_num = pd.to_numeric(grp_series.str[2:], errors="coerce")
    mask = (
        grp_series.str.startswith("ZG")
        & (grouping_num >= 1)
        & (grouping_num <= 13)
        & (grouping_num != 11)
    )
    # If the mask matches nothing (e.g., all NaN after merge), keep rows to avoid empty output.
    if mask.any():
        merged = merged[mask]
    if "country" in merged.columns:
        merged = merged[merged["country"].isin(["FR", None])]
    if "Name 1" in merged.columns:
        merged = merged[~merged["Name 1"].str.startswith("#", na=False)]
    if "First Name" in merged.columns:
        merged = merged[~merged["First Name"].str.startswith("#", na=False)]
    else :
        warn("Missing column 'First Name' in dataframe")
    if "Last Name" in merged.columns:
        merged = merged[~merged["Last Name"].str.startswith("#", na=False)]
    else :
        warn("Missing column 'Last Name' in dataframe")
    if "Search Term 1" in merged.columns:
        merged = merged[~merged["Search Term 1"].str.startswith("#", na=False)]
    else :
        warn("Missing column 'Search Term 1' in dataframe")
    if "BP" in merged.columns:
        merged = merged[~merged["BP"].str.startswith("0005", na=False)]

    #sets the missing columns
    merged = merged.apply(set_missing, axis=1)
    
    log("Merged tables and dropped non french and fr with creds")
    debug(merged[['BP', 'country']])
    
    return merged


def merge_address(datas: pd.DataFrame, join_table: pd.DataFrame, adress_table: pd.DataFrame):
    """
    Assemble les informations d'adresse en alignant les tables SAP comme dans partner_processing.py :
    deduplication des BPs avec le plus grand identifiant d'adresse, fusion des tables d'adresse,
    puis jointure vectorisee sur le DataFrame source.
    """
    # copies the dataframes to avoid modifying the originals
    datas = datas.copy()
    join_table = join_table.copy()
    adress_table = adress_table.copy()

    # Determine BP and Addr columns in each table
    bp_col_datas = "BP" if "BP" in datas.columns else ("Business Partner" if "Business Partner" in datas.columns else datas.columns[0])
    bp_col_join = "Business Partner" if "Business Partner" in join_table.columns else (join_table.columns[0] if len(join_table.columns) > 0 else None)
    addr_col_join = "Addr. No." if "Addr. No." in join_table.columns else join_table.columns[1]
    join_table = join_table.rename(columns={bp_col_join: "BP", addr_col_join: "Addr. No."})

    def _print_describe(label: str, frame: pd.DataFrame) -> None:
        debug(f"[describe] {label}")
        debug(frame.describe(include="all"))

    debug(f"[merge] main rows={len(datas)} bp_col_main={bp_col_datas}")
    debug(f"[merge] join rows={len(join_table)} bp_col_join={bp_col_join} addr_col_join={addr_col_join}")
    debug(f"[merge] address rows={len(adress_table)}")
    _print_describe("join_table (before merge)", join_table)

    # Vérification de la présence des colonnes nécessaires
    if bp_col_datas not in datas.columns:
        warn("[merge] main BP column missing, skipping address merge")
        return datas
    
    # Normalisation des colonnes BP dans les deux tables
    datas = datas.rename(columns={bp_col_datas: "BP"})
    datas["BP"] = datas["BP"].apply(_normalize_bp_value)

    if not bp_col_join or not addr_col_join:
        warn("[merge] join table missing BP/Addr columns, skipping address enrichment")
        return datas

    join_table = join_table.rename(columns={bp_col_join: "BP", addr_col_join: "Addr. No."})
    join_table["BP"] = join_table["BP"].apply(_normalize_bp_value)
    join_table["Addr. No."] = join_table["Addr. No."].apply(_normalize_addr_value)
    join_table = join_table[join_table["BP"] != ""]
    if join_table.empty:
        warn("[merge] join table empty after normalization, skipping address enrichment")
        return datas

    # Dropping duplicates: keep the latest Addr. No. per BP
    join_table = join_table.sort_values(by=["BP", "Addr. No."], ascending=[True, False])
    join_table = join_table.drop_duplicates(subset=["BP"])

    # Preparing the address table with necessary renaming and normalization for merging
    address_lookup = join_table[["BP", "Addr. No."]].copy()
    if not adress_table.empty:
        rename_map = {}
        if len(adress_table.columns) > 0:
            rename_map[adress_table.columns[0]] = "Addr. No."
        if len(adress_table.columns) > 26:
            rename_map[adress_table.columns[26]] = "street"
        if len(adress_table.columns) > 29:
            rename_map[adress_table.columns[29]] = "street4"
        if len(adress_table.columns) > 20:
            rename_map[adress_table.columns[20]] = "street5"
        if len(adress_table.columns) > 5:
            rename_map[adress_table.columns[5]] = "city"
        if len(adress_table.columns) > 4:
            rename_map[adress_table.columns[4]] = "postcode"
        if len(adress_table.columns) > 11:
            rename_map[adress_table.columns[11]] = "country"
        adress_table = adress_table.rename(columns=rename_map)
        _print_describe("adress_table (before merge)", adress_table)
        if "Addr. No." in adress_table.columns:
            adress_table["Addr. No."] = adress_table["Addr. No."].apply(_normalize_addr_value)
            keep_columns = [col for col in ("Addr. No.", "street", "street4", "street5", "city", "postcode", "country") if col in adress_table.columns]
            
            # Merging join_table with adress_table to get full address details
            address_lookup = pd.merge(left=join_table, right=adress_table[keep_columns], on="Addr. No.", how="left")
            _print_describe("join_table + adress_table (after merge)", address_lookup)
        else:
            warn("[merge] address table missing Addr. No., skipping address fields")
    else:
        warn("[merge] address table empty, keeping Addr. No. only")

    debug(f"[merge] address_lookup rows={len(address_lookup)}")

    # Final merge with the main datas table
    merged = pd.merge(datas, address_lookup, on="BP", how="left")
    merged = merged.rename(columns={"Addr. No.": "adressID"})
    _print_describe("datas (BUTO000) + address_lookup (after merge)", merged)
    debug(f"[merge] merged rows={len(merged)}")

    return merged

if __name__ == "__main__":
    # Set up logging
    logger = logger(mail=True, path=__file__, subject=SUBJECT)
    debug, log, warn, error = log_helpers(logger)
    try:
        log("Building dataset...")
        # Build the data
        df = build_data()
        
        # Create output directory with timestamp
        run_dir = Path(OUTPUT_DIR) / datetime.now().strftime("%Y-%m-%d_%H-%M_search")
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save initial data for reference
        infos = run_dir / "frenchBPs.xlsx"
        df.to_excel(infos, index=False)
        
        log(f"Got {len(df)} rows to preceed")
        debug(df[['BP', 'VAT', 'siret', 'siren', 'Name 1', 'missing siren', 'missing siret', 'missing vat']].describe(include='all'))
        # df = df[df['missing siren'] | df['missing siret'] | df['missing vat']]
        # df = df[~(df["missing siren"] & df["missing siret"] & df["missing vat"])].head(10)
        # df = df.tail(1500)
        # df = df.head(50)
        df['original missing siren'] = df['missing siren']
        df['original missing siret'] = df['missing siret']
        df['original missing vat'] = df['missing vat']
    except Exception:
        error("Data build failed", exc_info=True)
        raise
    #faire le tri ici pour vider les lignes avec des none nan ou vide
    df = df.apply(enrish_bp, logger=logger, axis=1)
    #df = df.apply(es.enrish_bp_geo_only, axis=1)
    try:
        col_order = [
            "BP",
            "Name 1",
            'original missing siren',
            'original missing siret',
            'original missing vat',
            "missing siren",
            "missing siret",
            "missing vat",
            "matching siren",
            "matching siret",
            "matching vat",
            "siren",
            "siret",
            "VAT",
            "score",
            "name score",
            "street score",
            "supposed right"
        ]
        for col in col_order:
            if col not in df.columns:
                df[col] = None
        df = df[col_order]

        out_file = run_dir / "missing_siren_found.xlsx"
        df.to_excel(out_file, index=False)
        log(f"Fichier enrichi ecrit dans: {out_file}")
        
        edited_file = run_dir / "missing_siren_found_to_edit.xlsx"
        edited = df[
            (df["missing siren"] != df["original missing siren"])
            | (df["missing siret"] != df["original missing siret"])
            | (df["missing vat"] != df["original missing vat"])
        ]
        edited.to_excel(edited_file, index=False)
        if edited.empty:send_quality_check_mail(subject=SUBJECT, body=NO_CHANGE_TEMPLATE, logger=logger)
        else:
            send_quality_check_mail(subject=SUBJECT, body=CHANGE_TEMPLATE, attachments=edited_file, logger=logger)
        log(f"Fichier édité ecrit dans: {edited_file}")
    except Exception:
        error("Failed to write output file", exc_info=True)
        raise
    

