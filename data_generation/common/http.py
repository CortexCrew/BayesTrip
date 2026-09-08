"""Shared HTTP session for the free OSM-ecosystem APIs (Nominatim, OSRM, Overpass).

Nominatim's usage policy requires a descriptive User-Agent and at most 1 request/sec;
the other two services are unauthenticated but are rate-limited the same way to be a
polite client.
"""

import time

import requests

USER_AGENT = "BayesTrip-DataPipeline/1.0 (student project; contact: su.sukanthan@gmail.com)"

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})

_last_request_at = 0.0
MIN_INTERVAL_SECONDS = 1.0


def get(url: str, params: dict | None = None, timeout: int = 15) -> requests.Response:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < MIN_INTERVAL_SECONDS:
        time.sleep(MIN_INTERVAL_SECONDS - elapsed)
    response = _session.get(url, params=params, timeout=timeout)
    _last_request_at = time.monotonic()
    response.raise_for_status()
    return response
