from thefuzz import fuzz
import pandas as pd

from format import format_name
from logger import logger as Logger

THRESHOLD = -1
WEIGHT_NAME = 0.5
WEIGHT_STREET = 0.35
WEIGHT_CITY = 0.15

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

    def _debug(msg):
        logger_obj.debug(msg)

    def _warn(msg):
        logger_obj.warn(msg)

    def _error(msg, exc_info=False):
        logger_obj.error(msg, exc_info=exc_info)

    return _debug, _warn, _error


def get_best_match(row: pd.Series, results, logger=None):
    _debug, _warn, _error = _log_helpers(logger)
    try:
        if not results or len(results) == 0:
            return None, None, None, None, None
        name = row.get("Name 1")
        name = format_name(name) if exists(name) else ""
        city = row.get("city")
        street = row.get("street")
        postcode = row.get("postcode")
        address = (street if exists(street) else "") + (" " + postcode if exists(postcode) else "") + (" " + city if exists(city) else "")
        best_match = None
        best_name_score = -1
        best_etab = None
        best_etab_score = -1
        best_street_score = -1
        best_combined = -1
        for i, soc in enumerate(results):
            name_score = max(
                fuzz.token_set_ratio(name, soc.get("nom_raison_sociale")),
                fuzz.token_set_ratio(name, soc.get("nom_complet")),
            )
            m_ets = soc.get("matching_etablissements") or []
            if city or address:
                etab_id = None
                etab_score = None
                street_score = None
                for j, etab in enumerate(m_ets):
                    city_score = None
                    if city:
                        city_score = fuzz.token_set_ratio(city, etab.get("libelle_commune"))
                    street_score = None
                    if address:
                        etab_addr = etab.get("adresse")
                        if etab_addr:
                            street_score = fuzz.token_set_ratio(address, etab_addr)
                    current_etab_score = None
                    if city_score is not None and street_score is not None:
                        current_etab_score = (city_score + street_score) / 2
                    elif city_score is not None:
                        current_etab_score = city_score
                    elif street_score is not None:
                        current_etab_score = street_score
                    if current_etab_score is not None and (etab_score is None or current_etab_score > etab_score):
                        etab_score = current_etab_score
                        etab_id = j
                        best_street_score = street_score if street_score is not None else -1
                if etab_id is not None:
                    total_weight = WEIGHT_NAME
                    combined = WEIGHT_NAME * name_score
                    if street_score is not None:
                        combined += WEIGHT_STREET * street_score
                        total_weight += WEIGHT_STREET
                    if city_score is not None:
                        combined += WEIGHT_CITY * city_score
                        total_weight += WEIGHT_CITY
                    combined = combined / total_weight if total_weight else name_score
                else:
                    combined = name_score
                if best_etab is not None and best_etab_score >= 0:
                    best_total_weight = WEIGHT_NAME
                    best_combined = WEIGHT_NAME * best_name_score
                    if best_street_score >= 0:
                        best_combined += WEIGHT_STREET * best_street_score
                        best_total_weight += WEIGHT_STREET
                    if best_etab_score >= 0:
                        best_combined += WEIGHT_CITY * best_etab_score
                        best_total_weight += WEIGHT_CITY
                    best_combined = best_combined / best_total_weight if best_total_weight else best_name_score
                else:
                    best_combined = best_name_score
                if combined > best_combined and name_score > THRESHOLD:
                    best_name_score = name_score
                    best_etab_score = etab_score if etab_score is not None else -1
                    best_etab = etab_id
                    best_match = i
                    best_combined = combined
            else:
                if name_score > best_name_score:
                    best_name_score = name_score
                    best_match = i
                    best_etab = 0 if m_ets else None
                    best_etab_score = 0 if m_ets else -1
                    best_street_score = -1

        if best_match is None:
            return None, None , None, None, None

        chosen = results[best_match]
        etabs = chosen.get("matching_etablissements") or []
        etab_city = (
            etabs[best_etab].get("libelle_commune") if etabs and best_etab is not None and best_etab < len(etabs) else "N/A"
        )
        _debug(f"best match for {name}, {city} : {chosen.get('nom_raison_sociale')}, {etab_city}.")
        return best_match, best_etab, best_combined, best_name_score, best_street_score
    except Exception:
        _error("get_best_match failed", exc_info=True)
        return None, None, None, None, None

def exists(col):
    if pd.isna(col):
        return False
    if isinstance(col, str):
        return col.strip().lower() not in ("", "none", "nan", "n/a", "---")
    return True
