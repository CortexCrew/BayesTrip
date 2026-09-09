"""Builds 02_BN_Prior: P(Place) from OpenTripMap popularity data.

For each place, OpenTripMap's `places/radius` endpoint is queried around its already
-geocoded coordinate (07_Coordinates) to find the matching POI and its `rate` field --
OpenTripMap's own 1-7h "how notable is this place" scale. `rate` is mapped to a numeric
score (RATE_SCALE below) and normalized across all 20 places to sum to 1.

This is deterministic once the raw `rate` values are fetched: the only judgment call is
picking the right POI out of the radius search results, which is done by exact/substring
name match first, falling back to the nearest result if no name match is found (logged
either way so the choice is auditable in 08_Evidence).

Requires the OPENTRIPMAP_API_KEY environment variable (free key from opentripmap.io).
"""

import os

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.http import get
from data_generation.common.workbook import read_sheet, write_sheet

BASE_URL = "https://api.opentripmap.com/0.1/en/places"
SEARCH_RADIUS_METERS = 500

# OpenTripMap's `rate` field mixes a numeric scale (0-3) with a lettered "highest
# importance" tier (1h/2h/3h/7h, used for globally notable places); mapped onto a
# single ordinal scale here so it can be normalized into a popularity score.
RATE_SCALE = {
    "0": 0.0,
    "1": 1.0,
    "2": 2.0,
    "3": 3.0,
    "1h": 4.0,
    "2h": 5.0,
    "3h": 6.0,
    "7h": 7.0,
}


def _api_key() -> str:
    key = os.environ.get("OPENTRIPMAP_API_KEY")
    if not key:
        raise SystemExit("OPENTRIPMAP_API_KEY is not set. Get a free key at https://opentripmap.io/product and export it.")
    return key


def _find_poi(lat: float, lng: float, name: str, api_key: str) -> dict:
    response = get(
        f"{BASE_URL}/radius",
        params={
            "radius": SEARCH_RADIUS_METERS,
            "lon": lng,
            "lat": lat,
            "limit": 15,
            "apikey": api_key,
            "format": "json",
        },
    )
    candidates = response.json()
    if not candidates:
        raise ValueError(f"OpenTripMap returned no POIs within {SEARCH_RADIUS_METERS}m of {name!r} ({lat}, {lng})")

    name_lower = name.lower()
    for c in candidates:
        c_name = (c.get("name") or "").lower()
        if c_name and (c_name in name_lower or name_lower in c_name):
            return c | {"match_method": "name substring match"}

    # No name match: fall back to the nearest candidate (radius results are
    # distance-sorted), which is still within SEARCH_RADIUS_METERS of the place.
    return candidates[0] | {"match_method": "nearest fallback (no name match)"}


def build() -> pd.DataFrame:
    api_key = _api_key()
    coords = read_sheet("07_Coordinates")

    rows = []
    for row in coords.itertuples():
        poi = _find_poi(row.lat, row.lng, row.name, api_key)
        rate = str(poi.get("rate", "0"))
        raw_score = RATE_SCALE.get(rate, 0.0)

        rows.append(
            {
                "place_id": row.place_id,
                "name": row.name,
                "opentripmap_xid": poi.get("xid"),
                "opentripmap_name": poi.get("name"),
                "opentripmap_rate": rate,
                "raw_score": raw_score,
                "match_method": poi["match_method"],
            }
        )

        log_evidence(
            agent="step03_bn_prior",
            place_id=row.place_id,
            variable="popularity",
            evidence_text=f"OpenTripMap rate={rate} for POI {poi.get('name')!r} (xid={poi.get('xid')}), {poi['match_method']}",
            source="OpenTripMap places/radius API",
            source_url=f"https://opentripmap.com/en/card/{poi.get('xid')}" if poi.get("xid") else BASE_URL,
        )
        print(f"{row.place_id} {row.name}: rate={rate} -> raw_score={raw_score} ({poi['match_method']})")

    df = pd.DataFrame(rows)
    total = df["raw_score"].sum()
    if total <= 0:
        raise ValueError("all OpenTripMap raw_scores are 0 -- cannot normalize into a prior")
    df["probability"] = df["raw_score"] / total
    return df


def main() -> None:
    df = build()
    assert abs(df["probability"].sum() - 1.0) < 1e-9, "probability does not sum to 1"
    write_sheet("02_BN_Prior", df)
    print(f"Wrote {len(df)} rows to 02_BN_Prior (sums to {df['probability'].sum():.6f})")


if __name__ == "__main__":
    main()
