"""Builds 07_Coordinates: location/coordinate data per place via the Geoapify Geocoding API.

Replaces the earlier OSM Nominatim-based implementation with Geoapify as the external
provider -- same step in the pipeline, same 20 places and place_ids, different provider.

For each place, the canonical name (data_generation/common/places.py) plus "Chennai,
Tamil Nadu, India" is sent to Geoapify's /v1/geocode/search endpoint, biased and filtered
to a 30km circle around Chennai Central so results are already constrained to the city.
Candidate results are then deterministically re-ranked (Geoapify's own rank.confidence,
then distance from Chennai Central as a tiebreak) and validated against three checks:
within MAX_DISTANCE_FROM_CENTER_KM of the city center, at or above MIN_CONFIDENCE
(Geoapify falls back to a low-confidence city/district-level match when it can't
resolve the actual POI -- e.g. "San Thome Basilica" once returned plain "Chennai" at
confidence 0.25), and containing the place's category word (the last significant word
of its canonical name, e.g. "Basilica", "House", "Temple" -- this catches same-area,
similar-name mismatches that still pass at high confidence, such as Geoapify matching
"Vivekananda House" to the unrelated "Vivekananda College"). If the primary query finds
no valid result, a known alternate query (data_generation/common/places.py's
`geocode_query` hints) is tried once as a fallback.

If no query resolves to a validated Chennai result, this script does NOT invent
coordinates: the row is written with empty latitude/longitude and confidence
"needs_manual_review" so it can be caught by 09_Validation and fixed by hand.
"""

import os
import re
from datetime import datetime, timezone
from math import atan2, cos, radians, sin, sqrt

import pandas as pd

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can also be exported directly

from data_generation.common.evidence import log_evidence
from data_generation.common.http import get
from data_generation.common.osrm import CHENNAI_CENTRAL
from data_generation.common.places import CITY, PLACES
from data_generation.common.workbook import write_sheet

GEOAPIFY_API_KEY_ENV = "GE0APIFY_API_KEY"  # exact spelling as specified: GE0APIFY (zero, not letter O)
GEOAPIFY_SEARCH_URL = "https://api.geoapify.com/v1/geocode/search"

SEARCH_RADIUS_METERS = 30_000  # server-side filter: only consider POIs within 30km of Chennai Central
MAX_DISTANCE_FROM_CENTER_KM = 40.0  # post-hoc validation threshold ("actually in/near Chennai")

# Geoapify falls back to a city/district-level match (result_type "city"/"suburb"/etc.,
# match_type "match_by_city_or_disrict") when it can't resolve the actual named POI --
# observed at confidence ~0.20-0.25 in practice, versus ~0.73-1.0 for genuine POI
# matches. Rejecting anything below this floor turns "found nothing useful" into a
# clean needs_manual_review instead of silently accepting the city center as the
# place's coordinate.
MIN_CONFIDENCE = 0.5
RESULT_LIMIT = 5

NEEDS_REVIEW = "needs_manual_review"


def _api_key() -> str:
    key = os.environ.get(GEOAPIFY_API_KEY_ENV)
    if not key:
        raise SystemExit(
            f"{GEOAPIFY_API_KEY_ENV} is not set. Get a free key at https://www.geoapify.com/ "
            f"and set it in a .env file (see .env.example) or export it directly."
        )
    return key


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))


def _geocode(query: str, api_key: str) -> list[dict]:
    response = get(
        GEOAPIFY_SEARCH_URL,
        params={
            "text": query,
            "apiKey": api_key,
            "filter": f"circle:{CHENNAI_CENTRAL['lng']},{CHENNAI_CENTRAL['lat']},{SEARCH_RADIUS_METERS}",
            "bias": f"proximity:{CHENNAI_CENTRAL['lng']},{CHENNAI_CENTRAL['lat']}",
            "limit": RESULT_LIMIT,
            "format": "json",
        },
    )
    return response.json().get("results", [])


def _category_word(place_name: str) -> str | None:
    """The last significant word of a place's canonical name (its category/type noun,
    e.g. "Basilica", "House", "Temple", "Zoo"/"Park"), used as a cheap but effective
    sanity check against same-area, similar-name mismatches. Parenthetical alt-names
    and a trailing ", Chennai" are stripped first so they don't dominate the result."""
    clean = re.sub(r"\([^)]*\)", "", place_name)
    clean = re.sub(rf",?\s*{re.escape(CITY)}\s*$", "", clean, flags=re.IGNORECASE).strip()
    words = re.findall(r"[A-Za-z']+", clean)
    if not words:
        return None
    word = words[-1].lower()
    return word if len(word) >= 3 else None


def _select_best(results: list[dict], place_name: str | None = None) -> dict | None:
    """Deterministic re-ranking: validate each candidate is within
    MAX_DISTANCE_FROM_CENTER_KM of Chennai Central, at or above MIN_CONFIDENCE
    (rejecting Geoapify's city/district-level fallback matches), and -- when
    place_name is given -- contains that place's category word (see _category_word).
    Among what remains, pick the highest rank.confidence, breaking ties by distance
    to the center. Returns None if no candidate validates."""
    category_word = _category_word(place_name) if place_name else None

    candidates = []
    for r in results:
        lat, lon = r.get("lat"), r.get("lon")
        if lat is None or lon is None:
            continue
        distance_km = _haversine_km(CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"], lat, lon)
        if distance_km > MAX_DISTANCE_FROM_CENTER_KM:
            continue
        confidence = (r.get("rank") or {}).get("confidence", 0.0)
        if confidence < MIN_CONFIDENCE:
            continue
        if category_word:
            result_text = f"{r.get('name') or ''} {r.get('formatted') or ''}".lower()
            if category_word not in result_text:
                continue
        candidates.append((confidence, -distance_km, distance_km, r))

    if not candidates:
        return None

    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)
    best_confidence, _, best_distance_km, best_result = candidates[0]
    return {"result": best_result, "confidence": best_confidence, "distance_km": best_distance_km}


def _request_url_for_evidence(query: str) -> str:
    # Same params as _geocode, minus the API key, so the exact request is traceable
    # without leaking the key into the workbook or evidence log.
    return (
        f"{GEOAPIFY_SEARCH_URL}?text={query}"
        f"&filter=circle:{CHENNAI_CENTRAL['lng']},{CHENNAI_CENTRAL['lat']},{SEARCH_RADIUS_METERS}"
        f"&bias=proximity:{CHENNAI_CENTRAL['lng']},{CHENNAI_CENTRAL['lat']}&limit={RESULT_LIMIT}&format=json"
    )


def _resolve_place(place: dict, api_key: str) -> dict:
    place_id, name = place["place_id"], place["name"]
    queries = [f"{name}, {CITY}, Tamil Nadu, India"]
    if place.get("geocode_query"):
        queries.append(place["geocode_query"])

    for attempt, query in enumerate(queries):
        results = _geocode(query, api_key)
        picked = _select_best(results, place_name=name)
        if picked is None:
            continue

        r = picked["result"]
        method = "primary query" if attempt == 0 else "fallback query"
        return {
            "place_id": place_id,
            "place_name": name,
            "search_query": query,
            "formatted_address": r.get("formatted", ""),
            "city": r.get("city", ""),
            "state": r.get("state", ""),
            "country": r.get("country", ""),
            "latitude": r.get("lat"),
            "longitude": r.get("lon"),
            "source": "Geoapify Geocoding API",
            "source_url": _request_url_for_evidence(query),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "confidence": picked["confidence"],
            "justification": (
                f"Selected via {method}: rank.confidence={picked['confidence']:.3f}, "
                f"{picked['distance_km']:.2f}km from Chennai Central (within {MAX_DISTANCE_FROM_CENTER_KM}km "
                f"validation threshold), geoapify place_id={r.get('place_id', 'n/a')}."
            ),
        }

    # No query produced a validated result: do not invent coordinates.
    last_query = queries[-1]
    return {
        "place_id": place_id,
        "place_name": name,
        "search_query": last_query,
        "formatted_address": "",
        "city": "",
        "state": "",
        "country": "",
        "latitude": None,
        "longitude": None,
        "source": "Geoapify Geocoding API",
        "source_url": _request_url_for_evidence(last_query),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "confidence": NEEDS_REVIEW,
        "justification": (
            f"No Geoapify result within {MAX_DISTANCE_FROM_CENTER_KM}km of Chennai Central for "
            f"{len(queries)} quer{'y' if len(queries) == 1 else 'ies'} tried ({'; '.join(map(repr, queries))}). "
            f"Coordinates intentionally left blank rather than guessed; needs manual review."
        ),
    }


def build() -> pd.DataFrame:
    api_key = _api_key()
    rows = []
    for place in PLACES:
        row = _resolve_place(place, api_key)
        rows.append(row)
        status = "OK" if row["latitude"] is not None else "NEEDS REVIEW"
        print(f"{row['place_id']} {row['place_name']}: [{status}] {row['justification']}")
    return pd.DataFrame(rows)


def main() -> None:
    df = build()

    for r in df.itertuples():
        log_evidence(
            agent="step02_coordinates",
            place_id=r.place_id,
            variable="coordinates",
            evidence_text=r.justification,
            source=r.source,
            source_url=r.source_url,
        )

    write_sheet("07_Coordinates", df)

    n_review = (df["confidence"] == NEEDS_REVIEW).sum()
    print(f"Wrote {len(df)} rows to 07_Coordinates ({n_review} flagged {NEEDS_REVIEW})")


if __name__ == "__main__":
    main()
