import requests as rq
from requests.exceptions import RequestException
import time

from logger import logger as Logger

API_URL = "https://recherche-entreprises.api.gouv.fr/search"

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


def request_api(
    params: dict,
    retries: int = 3,
    backoff: int = 5,
    url: str = API_URL,
    logger=None,
) -> rq.Response | None:
    """Call the search API with a small retry/backoff window on network errors."""
    _debug, _warn, _error = _log_helpers(logger)
    headers = {"accept": "application/json"}
    for attempt in range(retries):
        try:
            return rq.get(url, params=params, headers=headers, timeout=15)
        except RequestException as exc:
            if attempt == retries - 1:
                _warn(f"API request failed for {params}: {exc}")
                return None
            _debug(f"API request error attempt {attempt + 1}/{retries} for {params}: {exc}")
            time.sleep(backoff)
        except Exception:
            _error("request_api failed", exc_info=True)
            return None

