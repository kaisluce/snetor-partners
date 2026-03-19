"""Decoupe ZFAMILY / ZPRODUCER depuis le dernier EXPORT_*.xlsx.

Entree: dernier fichier EXPORT_*.xlsx du dossier.
Sorties: fichiers mis a jour dans outputs/ (uniquement si changement).
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from logger import log_helpers, logger as Logger

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATTERN = "EXPORT_*.xlsx"
OUTPUT_DIR = BASE_DIR / "outputs"
SUBJECT = "Family Producer"


def load_latest_export() -> tuple[pd.DataFrame, Path]:
    export_files = list(BASE_DIR.glob(INPUT_PATTERN))
    if not export_files:
        raise FileNotFoundError(
            f"Aucun fichier {INPUT_PATTERN} trouve dans {BASE_DIR}"
        )

    latest_export = max(export_files, key=lambda p: p.stat().st_mtime)
    df = pd.read_excel(latest_export, dtype=str).iloc[:, :4].copy()
    df.columns = ["Internal char no.", "Int counter values", "Int. counter", "Characteristic Value"]
    df = df.fillna("")
    return df, latest_export


def split_family_producer(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    first_col = df.columns[0]
    col_values = df[first_col].astype(str).str.upper().str.strip()

    # Filtre les deux segments attendus dans la premiere colonne.
    family_df = df[col_values == "ZFAMILY"].reset_index(drop=True)
    producer_df = df[col_values == "ZPRODUCER"].reset_index(drop=True)
    return family_df, producer_df


def get_latest_output(prefix: str) -> Path | None:
    files = list(OUTPUT_DIR.glob(f"{prefix}_updated_*.xlsx"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def is_equal_to_last(df: pd.DataFrame, prefix: str, log) -> bool:
    latest_file = get_latest_output(prefix)
    if latest_file is None:
        log(f"[{prefix}] Aucun fichier precedent.")
        return False

    previous_df = pd.read_excel(latest_file, dtype=str).fillna("")
    same = df.equals(previous_df)
    log(f"[{prefix}] Comparaison avec {latest_file.name}: {same}")
    return same


def save_output(df: pd.DataFrame, prefix: str, log) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Nom horodate pour conserver l'historique.
    output_file = OUTPUT_DIR / f"{prefix}_updated_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    df.to_excel(output_file, index=False)
    log(f"[{prefix}] Fichier enregistre: {output_file}")
    return output_file


def save_if_changed(df: pd.DataFrame, prefix: str, log) -> bool:
    if is_equal_to_last(df, prefix, log):
        log(f"[{prefix}] Pas de changement, rien a enregistrer.")
        return False
    save_output(df, prefix, log)
    return True


def main() -> None:
    app_logger = Logger(mail=False, subject=SUBJECT, path=__file__)
    _debug, log, _warn, error = log_helpers(app_logger)
    log("Demarrage du traitement Family Producer.")

    try:
        df, source_file = load_latest_export()
        log(f"Fichier source: {source_file.name}")
        log(f"Lignes source: {len(df)} (3 premieres colonnes gardees)")

        family_df, producer_df = split_family_producer(df)
        log(f"Lignes ZFAMILY: {len(family_df)}")
        log(f"Lignes ZPRODUCER: {len(producer_df)}")

        family_changed = save_if_changed(family_df, "ZFAMILY", log)
        producer_changed = save_if_changed(producer_df, "ZPRODUCER", log)

        if not family_changed and not producer_changed:
            log("Aucun changement detecte sur ZFAMILY et ZPRODUCER.")
    except Exception as exc:
        error(f"Echec du traitement: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
