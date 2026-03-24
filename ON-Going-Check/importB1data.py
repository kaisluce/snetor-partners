from datetime import date
from typing import Iterable

import pandas as pd
import pyodbc
from logger import log_helpers

SERVER = "192.168.20.18"
DATABASES = [
    "SNSH",
    "SNAS",
    "SNBLK",
    "SNGPBX",
    "SNCHILI",
    "SNCO",
#    "SNCI",
    "SNUG",
    "SNEA",
    "SNGPRO",
    "SNEC",
    "SNEGY",
    "SNDE",
    "SNKR",
    "SNEMA",
    "SNOM",
    "SNMX",
    "SNME",
    "SNGPSE",
    "SNPE",
    "SNUS",
    "SNWA",
    "SNES",
    "SNPO"
]

USERNAME = "SneDataReader"
PASSWORD = "HDveJ3h7"

PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server",
]


def _pick_driver() -> str:
    installed = set(pyodbc.drivers())
    for d in PREFERRED_DRIVERS:
        if d in installed:
            return d
    raise RuntimeError(
        "No SQL Server ODBC driver found. Installed drivers: "
        + ", ".join(sorted(installed))
    )


def _build_conn_str(driver: str, database: str) -> str:
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={SERVER};"
        f"DATABASE={database};"
        f"UID={USERNAME};PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )


def _load_partner_changes_for_database(
    date_debut_sql: str, date_fin_sql: str, database: str, driver: str, logger=None
) -> pd.DataFrame:
    _debug, _log, _warn, _error = log_helpers(logger)
    _log(f"[B1] -> DB: {database}")
    conn_str = _build_conn_str(driver, database)
    sql = f"SET NOCOUNT ON; EXEC [{database}].[dbo].[SNE_Partners_Changes_Log] ?, ?"

    with pyodbc.connect(conn_str) as conn:
        cur = conn.cursor()
        _log(f"[B1] DB {database}: executing procedure...")
        try:
            cur.execute(sql, (date_debut_sql, date_fin_sql))
        except Exception as exc:
            _warn(f"[B1] DB {database}: ERROR - {exc}")
            return pd.DataFrame()
        _log(f"[B1] DB {database}: execute done")

        while cur.description is None:
            _log(f"[B1] DB {database}: waiting for result set... (cur.description is none)")
            if not cur.nextset():
                _log(f"[B1] DB {database}: no result set")
                return pd.DataFrame()

        columns = [col[0] for col in cur.description]
        _log(f"[B1] DB {database}: fetching result set...")
        rows = cur.fetchall()
        _log(f"[B1] DB {database}: fetch done")
        df = pd.DataFrame.from_records(rows, columns=columns)
        if not df.empty:
            df["source_database"] = database
        _log(f"[B1] DB {database}: {len(df)} rows")
        return df


def load_partner_changes(
    date_debut: date, date_fin: date, databases: Iterable[str] | None = None, logger=None
) -> pd.DataFrame:
    _debug, _log, _warn, _error = log_helpers(logger)
    try:
        selected_databases = [db.strip() for db in (databases or DATABASES) if db and db.strip()]
        if not selected_databases:
            raise ValueError("No database provided in `databases`/`DATABASES`.")

        _log("[B1] Starting stored procedure calls...")
        _log(f"[B1] Server: {SERVER}")
        _log(f"[B1] Period: {date_debut} -> {date_fin}")
        _log(f"[B1] Databases count: {len(selected_databases)}")

        driver = _pick_driver()
        _log(f"[B1] ODBC driver selected: {driver}")

        date_debut_sql = date_debut.strftime("%Y%m%d")
        date_fin_sql = date_fin.strftime("%Y%m%d")

        all_frames: list[pd.DataFrame] = []
        failed_databases: list[str] = []

        for database in selected_databases:
            try:
                df_db = _load_partner_changes_for_database(
                    date_debut_sql, date_fin_sql, database, driver, logger=logger
                )
                if not df_db.empty:
                    all_frames.append(df_db)
            except Exception as exc:
                failed_databases.append(database)
                _error(f"[B1] DB {database}: ERROR - {exc}", exc_info=True)

        consolidated = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
        consolidated = consolidated.drop_duplicates(subset=["Nom Partenaire"])
        _log(f"[B1] Consolidated rows: {len(consolidated)}")
        if failed_databases:
            _log(f"[B1] Failed databases ({len(failed_databases)}): {', '.join(failed_databases)}")
        return consolidated
    except Exception as exc:
        _error(f"[B1] Fatal error in load_partner_changes: {exc}", exc_info=True)
        raise


if __name__ == "__main__":
    from logger import logger as app_logger

    log = app_logger()
    _debug, _log, _warn, _error = log_helpers(log)
    try:
        df = load_partner_changes(date(2022, 2, 1), date(2026, 2, 18), logger=log)
        _log(f"[B1] Sample:\n{df.head().to_string(index=False)}")
        _log(f"[B1] Rows: {len(df)}")
    except Exception as exc:
        _error(f"[B1] ERROR: {exc}", exc_info=True)
        raise
