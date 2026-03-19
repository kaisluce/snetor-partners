import re

import pandas as pd

from get_best_match import get_best_match
from request_by import request_by_postcode, request_by_departement, request_by_name, request_by_coordinates
from format import format_name, format_postcode
from recherche_cord import get_coordinates

from requestFromSiren import handlesiren
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

def exists(col):
    if pd.isna(col):
        return False
    if isinstance(col, str):
        return col.strip().lower() not in ("", "none", "nan", "n/a", "---")
    return True

def find_siren(row: pd.Series, logger=None) -> pd.Series:
    _info, _debug, _warn, _error = _log_helpers(logger)

    def apply_results(results, source: str) -> bool:
        try:
            if results and len(results) > 0:
                best_match, best_etab, score, name_score, street_score = get_best_match(
                    row, results, logger=logger
                )
                if best_match is None:
                    _debug(f"aucun match fiable pour {name}")
                    return False
                chosen = results[best_match]
                etabs = chosen.get("matching_etablissements") or []
                siren_val = chosen.get("siren")
                siret_val = None
                if best_etab is not None and best_etab < len(etabs):
                    siret_val = etabs[best_etab].get("siret")
                # Fallback : l'API fournit souvent siret_siege quand matching_etablissements est vide
                if not siret_val:
                    siret_val = chosen.get("siret_siege") or (chosen.get("siege") or {}).get("siret")
                if not siret_val:
                    _warn(f"aucun etablissement exploitable pour {name}")
                    return False
                row["matching siren"] = siren_val
                row["matching siret"] = siret_val
                row["score"] = score
                row["name score"] = name_score
                row["street score"] = street_score
                row["supposed right"] = name_score >= 85
                _info(
                    f"answer ({source}) : siren : {row['matching siren']} siret : {row['matching siret']}"
                )
                return True
            return False
        except Exception:
            _error("apply_results failed", exc_info=True)
            return False

    try:
        _info(
            "requesting BP {partner} : {siret}, {siren}, {vat}".format(
                partner=row.get("partner"),
                siret=row.get("siret"),
                siren=row.get("siren"),
                vat=row.get("VAT"),
            )
        )
        name = row.get("Name 1")
        if not exists(name):
            return row

        postcode_param = format_postcode(row.get("postcode")) if exists(row.get("postcode")) else None
        departement = postcode_param[:2] if postcode_param and len(postcode_param) >= 2 else None
        _debug(f"trying with name and postcode: {format_name(name)} - {postcode_param}")

        # Ordre de recherche : code postal > departement > nom seul > adresse (coords GPS).
        res = request_by_postcode(str(name), postcode_param) if postcode_param else None
        if res and res.status_code == 200:
            data = res.json()
            results = data.get("results") or []
        elif res:
            _warn(f"postcode request failed with status {res.status_code}")
            results = []
        else:
            results = []

        if apply_results(results, "postcode"):
            return row

        if departement:
            _debug(
                "unable to find with postcode, trying with departement: {name} - {departement}".format(
                    name=str(name),
                    departement=departement,
                )
            )
            res = request_by_departement(str(name), departement)
            if res and res.status_code == 200:
                data = res.json()
                results = data.get("results") or []
            elif res:
                _warn(f"departement request failed with status {res.status_code}")
                results = []
            else:
                results = []

            if apply_results(results, "departement"):
                return row

        _debug(
            "unable to find with departement or postcode, trying with name only {name}".format(
                name=str(name)
            )
        )

        # If nothing is found by postcode or departement, this is the process to treat it with only the name:
        res = request_by_name(str(name))
        if res and res.status_code == 200:
            data = res.json()
            results = data.get("results") or []
        elif res:
            _warn(f"name request failed with status {res.status_code}")
            results = []
        else:
            results = []

        if apply_results(results, "name"):
            return row

        coords = get_coordinates(row, logger=logger)
        if coords:
            for radius in (0.01, 0.05, 0.1):
                _debug(f"nom non trouve, tentative via adresse et near_point {coords} r={radius}")
                lon = coords[0]
                lat = coords[1]
                res = request_by_coordinates(lon, lat, radius=radius)
                if res and res.status_code == 200:
                    data = res.json()
                    results = data.get("results") or []
                    _debug(f"results with radius {radius}:")
                    for result in results:
                        _debug(str(result.get("nom_raison_sociale")))
                elif res:
                    _warn(f"near_point request failed with status {res.status_code}")
                    results = []
                else:
                    results = []

                if apply_results(results, f"near_point r={radius}"):
                    return row
        else:
            _debug(f"aucune adresse exploitable pour {name}")

        _debug(f"no results at all for {name}")
        return row
    except Exception:
        _error("find_siren failed", exc_info=True)
        return row

def calculate_Vat(siren: str) -> str:
    digits = re.sub(r"\D+", "", str(siren) if siren is not None else "")
    if not digits:
        return None
    if len(digits) != 9:
        return None
    key = (12 + 3 * (int(digits) % 97)) % 97
    return f"FR{key:02d}{digits}"

def enrish_bp(row: pd.Series, logger=None) -> pd.Series:
    _info, _debug, _warn, _error = _log_helpers(logger)
    try:
        _info(f"Enriching BP : {row['BP']}")
        if (row["missing siren"] and row["missing siret"] and row["missing vat"]):
            # Cas 1: siren + siret + vat manquants -> recherche complete via find_siren
            _info(f"Looking for all missing informations about BP : {row['BP']}")
            row = find_siren(row, logger=logger)
            if row.get("matching siren"):
                _info("Found siren and siret, updating 'missing' columns")
                row["missing siren"] = False
                row["missing siret"] = False

        if row["missing siren"] and not (row["missing siret"]):
            # Cas 2: siren manquant, siret present -> extraire le siren depuis le siret
            _info(f"Getting the missing siren from the siret for BP : {row['BP']}")
            row["matching siren"] = row["siret"][:9]
            row["missing siren"] = False

        if row["missing siren"] and not (row["missing vat"]):
            # Cas 3: siren manquant, vat present -> extraire le siren depuis le vat
            _info(f"Getting the missing siren from the vat for BP : {row['BP']}")
            row["matching siren"] = row["VAT"][4:]
            row["missing siren"] = False

        if row["missing vat"] and not (row["missing siren"] and row["missing siret"]):
            # Cas 5: vat manquant, mais on a au moins siren ou siret
            _info(f"Calculating the missing vat for BP : {row['BP']}")
            if not row.get("missing siren"):
                if row.get("matching siren"):
                    row["matching vat"] = calculate_Vat(row.get("matching siren"))
                else:
                    row["matching vat"] = calculate_Vat(row.get("siren"))
            else:
                if row.get("matching siret"):
                    row["matching vat"] = calculate_Vat(row.get("matching siret"))
                else:
                    row["matching vat"] = calculate_Vat(row.get("siret"))
            row["missing vat"] = False

        if row["missing siret"] and not (row["missing siren"]):
            # Cas 6: siret manquant, siren present -> interroger siren api pour obtenir le siret
            _info(f"Looking for the missing siret from the siren for BP : {row['BP']}")
            row = handlesiren(row, logger=logger)
        if not (row["missing siren"] and row["missing siret"] and row["missing vat"]):
            # Cas 4: rien a completer pour siren/siret/vat
            _info(f"No siren/siret/vat missing for BP : {row['BP']}")
        return row
    except Exception:
        _error("enrish_bp failed", exc_info=True)
        return row
