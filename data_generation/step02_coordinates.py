"""Builds 07_Coordinates: lat/lng per place via OSM Nominatim geocoding."""

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.http import get
from data_generation.common.places import CITY, PLACES
from data_generation.common.workbook import write_sheet

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode(query: str) -> dict:
    response = get(NOMINATIM_URL, params={"q": query, "format": "json", "limit": 1})
    results = response.json()
    if not results:
        raise ValueError(f"Nominatim returned no results for query: {query!r}")
    return results[0]


def build() -> pd.DataFrame:
    rows = []
    for p in PLACES:
        if "geocode_override" in p:
            lat, lng = p["geocode_override"]
            source = "OSM Overpass (name-substring search; not indexed by Nominatim)"
            query = None
        else:
            query = p.get("geocode_query", f"{p['name']}, {CITY}, India")
            result = geocode(query)
            lat, lng = float(result["lat"]), float(result["lon"])
            source = "OSM Nominatim"

        rows.append(
            {
                "place_id": p["place_id"],
                "name": p["name"],
                "lat": lat,
                "lng": lng,
                "source": source,
                "geocode_query": query,
            }
        )
        print(f"{p['place_id']} {p['name']}: {lat}, {lng}")
    return pd.DataFrame(rows)


def main() -> None:
    df = build()

    for r in df.itertuples():
        log_evidence(
            agent="step02_coordinates",
            place_id=r.place_id,
            variable="coordinates",
            evidence_text=f"lat={r.lat}, lng={r.lng}" + (f" for query {r.geocode_query!r}" if r.geocode_query else ""),
            source=r.source,
            source_url="https://nominatim.openstreetmap.org/ui/search.html?q=" + (r.geocode_query or r.name),
        )

    write_sheet("07_Coordinates", df.drop(columns=["geocode_query"]))
    print(f"Wrote {len(df)} rows to 07_Coordinates")


if __name__ == "__main__":
    main()
