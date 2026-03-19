from format import format_postcode, clean_address_component

from requests.exceptions import RequestException
import pandas as pd
import requests as rq
import re
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

    def _debug(msg):
        logger_obj.debug(msg)

    def _warn(msg):
        logger_obj.warn(msg)

    def _error(msg, exc_info=False):
        logger_obj.error(msg, exc_info=exc_info)

    return _debug, _warn, _error


def get_coordinates(bp: pd.Series, logger=None) -> tuple[float, float] | None:
    """
    Geocode a BP row with api-adresse; returns (long, lat) or None when unavailable.
    """
    _debug, _warn, _error = _log_helpers(logger)
    try:
        url = "https://api-adresse.data.gouv.fr/search"

        # street_parts = []
        # for key in ("street", "street4", "street5"):
        #     if _usable(key):
        #         cleaned = clean_address_component(bp.get(key))
        #         if cleaned:
        #             street_parts.append(cleaned)
        street = bp.get("street")
        city = clean_address_component(bp.get("city"), logger=logger)
        city = re.sub(r"\d+", "", city)
        postcode = format_postcode(bp.get("postcode"), logger=logger)
        if not street:
            return None
        params = {"q": street, "limit": 1}
        if city:
            params["city"] = city
        if postcode:
            params["postcode"] = postcode
        _debug(f"geocoding {params}")
        try:
            resp = rq.get(url, params=params, timeout=15)
            if resp.status_code != 200:
                _warn(f"geocode failed (status {resp.status_code}) for {params}")
                data = None
            else:
                data = resp.json()
        except RequestException as exc:
            _warn(f"unable to geocode {street}: {exc}")
            data = None
        except ValueError:
            _warn(f"invalid geocode response for {street}")
            data = None
        features = data.get("features") if isinstance(data, dict) else None
        if not features:
            return try_without_postcode(bp, logger=logger)
        geom = features[0].get("geometry") or {}
        coords = geom.get("coordinates")
        _debug(f"geocoded to {coords}")
        if coords and len(coords) >= 2:
            try:
                return float(coords[0]), float(coords[1])
            except (TypeError, ValueError):
                return try_without_postcode(bp, logger=logger)
        elif bp.get("postcode"):
            return try_without_postcode(bp, logger=logger)
        return None
    except Exception:
        _error("get_coordinates failed", exc_info=True)
        return None


def try_without_postcode(bp: pd.Series, logger=None) -> tuple[float, float] | None:
    if bp.get("postcode"):
        # refaire une ligne mais sans le postcode
        retry = bp.copy()
        retry["postcode"] = None
        return get_coordinates(retry, logger=logger)
    return None


def try_without_city(bp: pd.Series, logger=None) -> tuple[float, float] | None:
    if bp.get("city"):
        # refaire une ligne mais sans le postcode
        retry = bp.copy()
        retry["city"] = None
        return get_coordinates(retry, logger=logger)
    return None
