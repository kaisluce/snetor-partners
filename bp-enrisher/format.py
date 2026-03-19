import re
import pandas as pd

from logger import logger as Logger

REMOVE_WORDS = {
    "sa",
    "sas",
    "sarl",
    "inc",
    "co",
    "srl",
    "ets",
    "etablissement",
    "‚tablissement",
    "ste",
    "societe",
    "soci‚t‚",
    "nouvelle"
}

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


def format_name(name: str, logger=None) -> str:
    """Normalize a name by lower/strip and removing stop-words."""
    _debug, _warn, _error = _log_helpers(logger)
    try:
        if not isinstance(name, str):
            name = "" if name is None else str(name)
        cleaned = name.lower().strip()
        if not cleaned:
            return ""
        tokens = re.split(r"\s+", cleaned)
        tokens = [t for t in tokens if t and t not in REMOVE_WORDS]
        return " ".join(tokens)
    except Exception:
        _error("format_name failed", exc_info=True)
        return ""


def format_postcode(value, logger=None) -> str | None:
    """Clean a postcode and restore leading zeros (zfill)."""
    _debug, _warn, _error = _log_helpers(logger)
    try:
        if value is None or pd.isna(value):
            return None
        s = str(value).strip()
        if not s:
            return None
        digits = re.sub(r"\D", "", s)
        if not digits:
            return None
        if len(digits) < 5:
            digits = digits.zfill(5)
        _debug(f"cleaned postcode: {str(value)} -> {digits}")
        return digits
    except Exception:
        _error("format_postcode failed", exc_info=True)
        return None


def clean_address_component(value, logger=None):
    """Remove Cedex/CS/BP markers and related numbering from an address field."""
    _debug, _warn, _error = _log_helpers(logger)
    try:
        if value is None or pd.isna(value):
            return ""
        s = str(value)
        s = re.sub(r"\bcedex\b.*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\bcs\s*\d*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\bbp\s*\d*", "", s, flags=re.IGNORECASE)
        _debug(f"cleaned address component: {str(value)} -> {s}")
        return s
    except Exception:
        _error("clean_address_component failed", exc_info=True)
        return ""
