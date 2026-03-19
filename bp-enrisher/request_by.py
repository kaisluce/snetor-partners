from recherche_soc_api import request_api
from format import format_name

import requests as rq


def request_by_postcode(name: str, postcode: str, retries: int = 3, backoff: int = 5) -> rq.Response | None:
    sanitized = format_name(name)
    params = {"q": sanitized, 'limit' : 25, "page": 1, "per_page": 25, "code_postal": postcode.strip()}
    return request_api(params, retries=retries, backoff=backoff)


def request_by_departement(name: str, departement: str, retries: int = 3, backoff: int = 5) -> rq.Response | None:
    sanitized = format_name(name)
    params = {"q": sanitized, 'limit' : 25, "page": 1, "per_page": 25, "departement": departement.strip()}
    return request_api(params, retries=retries, backoff=backoff)


def request_by_name(name: str, retries: int = 3, backoff: int = 5) -> rq.Response | None:
    sanitized = format_name(name)
    params = {"q": sanitized, 'limit' : 25, "page": 1, "per_page": 25, }
    return request_api(params, retries=retries, backoff=backoff)

def request_by_coordinates(
    longitude: float,
    latitude: float,
    radius: float = 0.1,
    limit: int = 25,
    per_page: int = 25,
    page: int = 1,
    retries: int = 3,
    backoff: int = 5,
) -> rq.Response | None:
    params = {"long": longitude, "lat": latitude, "radius": radius, "limit": limit, "per_page": per_page, "page": page}
    return request_api(
        params,
        retries=retries,
        backoff=backoff,
        url="https://recherche-entreprises.api.gouv.fr/near_point",
    )