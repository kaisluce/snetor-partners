import time
from typing import Any, Dict

import requests as rq
from requests.exceptions import RequestException

from thefuzz import fuzz

import pandas as pd
from logger import logger as Logger

_DEFAULT_LOGGER = None


def _get_logger(logger=None):
    global _DEFAULT_LOGGER
    if logger is not None:
        return logger
    if _DEFAULT_LOGGER is None:
        _DEFAULT_LOGGER = Logger()
    return _DEFAULT_LOGGER


def _log_helpers(logger=None):
    logger_obj = _get_logger(logger)

    def _info(msg):
        logger_obj.log(msg)

    def _debug(msg):
        logger_obj.debug(msg)

    def _warn(msg):
        logger_obj.warn(msg)

    def _error(msg, exc_info=False):
        logger_obj.error(msg, exc_info=exc_info)

    return _info, _debug, _warn, _error


def _get_with_retry(url: str, delay: int = 3, max_durations: int = 600, logger=None):
    _info, _debug, _warn, _error = _log_helpers(logger)
    try:
        start = time.time()
        attempt = 0
        while time.time() - start < max_durations:
            try:
                response = rq.get(url)
            except RequestException as exc:
                _warn(f"RequestException on attempt {attempt} for URL {url}: {exc}")
                attempt += 1
                time.sleep(delay)
                continue
            if response is not None:
                if response.status_code == 200:
                    return response
                _warn(f"Received status code {response.status_code} on attempt {attempt} for URL {url}")
                if response.status_code == 401:
                    response = rq.options(url)
                    try:
                        if response is not None and response.status_code == 200:
                            return None
                    except RequestException:
                        continue
                if response.status_code == 400:
                    return None
            attempt += 1
            time.sleep(delay)
        return None
    except Exception:
        _error("_get_with_retry failed", exc_info=True)
        return None


def handlesiren(row: pd.Series, logger=None) -> Dict[str, Any]:
    """Query the SIRENE API using a SIREN number and enrich the row."""
    _info, _debug, _warn, _error = _log_helpers(logger)
    try:
        if row.get("siren") and len(row["siren"]) == 9:
            siren = row["siren"]
        else:
            siren = row.get("matching siren")
        if siren and len(siren) != 9:
            _warn(f"SIREN invalide: {siren}")
            return row
        url = f"https://api-avis-situation-sirene.insee.fr/identification/siren/{siren}?telephone="

        response = _get_with_retry(url, logger=logger)
        if response is not None and response.status_code == 200:
            data = response.json()
            etabs = data["etablissements"]
            best_street_score = -1
            best_city_score = -1
            best_etab = None
            row_street = row.get("street", "")
            row_city = row.get("city", "")
            if pd.isna(row_street):
                row_street = ""
            if pd.isna(row_city):
                row_city = ""
            row_street = str(row_street).strip().lower()
            row_city = str(row_city).strip().lower()
            for etab in etabs:
                address = etab.get("adresseEtablissement")
                if not address:
                    continue
                street = (
                    f"{address.get('numeroVoieEtablissement') or ''} "
                    f"{address.get('typeVoieEtablissement') or ''} "
                    f"{address.get('libelleVoieEtablissement') or ''}"
                ).strip().lower()
                city = str(address.get("libelleCommuneEtablissement") or "").strip().lower()
                current_street_score = fuzz.token_set_ratio(row_street, street)
                current_city_score = fuzz.token_set_ratio(row_city, city)
                if 0.8 * current_street_score + 0.2 * current_city_score > 0.8 * best_street_score + 0.2 * best_city_score:
                    best_street_score = current_street_score
                    best_city_score = current_city_score
                    best_etab = etab
            row["matching siret"] = best_etab.get("siret") if best_etab else None
            if row["matching siret"]:
                _info(
                    "Found siret {siret} for siren {siren}".format(
                        siret=row["matching siret"],
                        siren=row.get("siren", row.get("matching siren", "")),
                    )
                )
                row["missing siret"] = False
            return row
        _warn(
            "Failed to retrieve data for SIREN {siren}. Status code: {status}".format(
                siren=row.get("siren", row.get("matching siren", "")),
                status=response.status_code if response else "No Response",
            )
        )
        return row
    except Exception:
        _error("handlesiren failed", exc_info=True)
        return row


if __name__ == "__main__":
    _info, _debug, _warn, _error = _log_helpers()
    try:
        df = pd.read_excel(r"Z:\MDM\998_CHecks\AUTOCHECKS\2026-01-14_10-01_REPORT\latest_datas.xlsx").astype(str)
        df["missing siren"] = df["missing siren"] == "True"
        df["missing siret"] = df["missing siret"] == "True"
        df = df[df["country"] == "FR"]
        _info("looking for sirets")
        df = df.tail(1600)
        df = df.head(10)
        _debug(df)
        df = df.apply(lambda row: handlesiren(row, logger=_get_logger()), axis=1)
        output_path = r"C:\Users\K.luce\Downloads\siren_to_siret.xlsx"
        df.to_excel(output_path, index=False)
        _info(f"Fichier enrichi ecrit dans: {output_path}")
        nb = len(df["siret"])
        _info(f"{len(df['matching siret'] == df['siret'])} / {nb} sirets trouves")
        _debug(df)
    except Exception:
        _error("requestFromSiren __main__ failed", exc_info=True)
