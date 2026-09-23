
from datetime import datetime, timezone

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.osrm import CHENNAI_CENTRAL, distance_duration_matrix
from data_generation.common.places import PLACES
from data_generation.common.workbook import read_sheet, write_sheet

DISTANCE_METHOD = "OSRM road routing (table service, driving profile): distance and travel time both from the same OSRM response"
SOURCE = "OSRM public routing API (table service)"
SOURCE_URL = "https://router.project-osrm.org/table/v1/driving/"

EPSILON = 0.01  # minutes; prevents division by zero, negligible next to any real travel time


def _load_coordinates() -> pd.DataFrame:
    coords = read_sheet("07_Coordinates")

    non_geoapify = coords[coords["source"] != "Geoapify Geocoding API"]
    if not non_geoapify.empty:
        raise ValueError(
            "07_Coordinates contains rows not sourced from Geoapify Geocoding API "
            f"(found: {non_geoapify['source'].unique().tolist()}) -- refusing to use "
            "stale/non-final coordinates (e.g. old Nominatim data)."
        )

    missing_coords = coords[coords["latitude"].isna() | coords["longitude"].isna()]
    if not missing_coords.empty:
        raise ValueError(
            f"07_Coordinates has {len(missing_coords)} place(s) with missing latitude/longitude "
            f"(place_id(s): {missing_coords['place_id'].tolist()}) -- cannot compute pi for them. "
            "Resolve those coordinates before running this step."
        )

    return coords


def build() -> pd.DataFrame:
    coords = _load_coordinates()

    canonical_ids = {p["place_id"] for p in PLACES}
    coord_ids = set(coords["place_id"])
    if coord_ids != canonical_ids:
        raise ValueError(f"07_Coordinates place_ids {coord_ids} do not match the canonical list {canonical_ids}")
    if coords["place_id"].duplicated().any():
        raise ValueError(f"07_Coordinates has duplicate place_id values: {coords.loc[coords['place_id'].duplicated(), 'place_id'].tolist()}")
    if len(coords) != 20:
        raise ValueError(f"Expected exactly 20 destinations, found {len(coords)}")

    points = [{"lat": CHENNAI_CENTRAL["lat"], "lng": CHENNAI_CENTRAL["lng"]}]
    points += [{"lat": row.latitude, "lng": row.longitude} for row in coords.itertuples()]

    distances_m, durations_s = distance_duration_matrix(points)
    # Row 0 = Chennai Central; columns 1..N = the 20 places, in coords' row order.
    distances_from_central_m = distances_m[0][1:]
    durations_from_central_s = durations_s[0][1:]

    retrieved_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for row, distance_m, duration_s in zip(coords.itertuples(), distances_from_central_m, durations_from_central_s):
        has_route = distance_m is not None and duration_s is not None
        distance_km = round(distance_m / 1000.0, 3) if has_route else None
        travel_time_min = round(duration_s / 60.0, 3) if has_route else None

        if has_route:
            raw_score = 1.0 / (travel_time_min + EPSILON)
            confidence = "high"
            justification = (
                f"Destination is approximately {distance_km:.2f} km ({travel_time_min:.1f} min driving) "
                f"from Chennai Central Railway Station via OSRM road routing. The accessibility score is "
                f"calculated using the predefined inverse-travel-time formula "
                f"(1 / (travel_time_min + {EPSILON})), then normalized across all 20 destinations."
            )
        else:
            raw_score = None
            confidence = "needs_manual_review"
            justification = (
                "OSRM could not find a route from Chennai Central Railway Station to this destination "
                "(no distance/duration returned). No value was fabricated; this place is excluded from "
                "the pi normalization until a route is available."
            )

        rows.append(
            {
                "place_id": row.place_id,
                "place_name": row.place_name,
                "start_location": CHENNAI_CENTRAL["name"],
                "start_latitude": CHENNAI_CENTRAL["lat"],
                "start_longitude": CHENNAI_CENTRAL["lng"],
                "place_latitude": row.latitude,
                "place_longitude": row.longitude,
                "distance_km": distance_km,
                "travel_time_min": travel_time_min,
                "raw_accessibility_score": raw_score,
                "distance_method": DISTANCE_METHOD,
                "source": SOURCE,
                "source_url": SOURCE_URL,
                "retrieved_at": retrieved_at,
                "justification": justification,
                "confidence": confidence,
            }
        )
        print(f"{row.place_id} {row.place_name}: {distance_km} km, {travel_time_min} min -> raw_score={raw_score}")

    df = pd.DataFrame(rows)
    total_score = df["raw_accessibility_score"].sum(skipna=True)
    df["initial_probability"] = df["raw_accessibility_score"] / total_score
    return df


def _validate(df: pd.DataFrame) -> None:
    canonical_ids = {p["place_id"] for p in PLACES}
    assert len(df) == 20, f"expected exactly 20 destinations, got {len(df)}"
    assert set(df["place_id"]) == canonical_ids, "place_ids do not match the canonical list"
    assert not df["place_id"].duplicated().any(), "duplicate place_id values found"
    assert df["place_latitude"].notna().all() and df["place_longitude"].notna().all(), "missing place coordinates"
    assert (df["distance_method"] == DISTANCE_METHOD).all(), "distance method is not uniform/OSRM-only"
    assert (df["start_location"] == CHENNAI_CENTRAL["name"]).all(), "start_location is not Chennai Central Railway Station"

    valid = df["distance_km"].notna()
    assert (df.loc[valid, "distance_km"] >= 0).all(), "negative distance found"
    assert (df.loc[valid, "travel_time_min"] >= 0).all(), "negative travel time found"

    probs = df.loc[valid, "initial_probability"]
    assert ((probs >= 0) & (probs <= 1)).all(), "a probability is outside [0, 1]"
    prob_sum = probs.sum()
    assert abs(prob_sum - 1.0) < 1e-9, f"initial_probability does not sum to 1 (sum={prob_sum})"

    required_fields = [
        "place_id", "place_name", "start_location", "start_latitude", "start_longitude",
        "place_latitude", "place_longitude", "distance_method", "source", "source_url",
        "retrieved_at", "justification", "confidence",
    ]
    for field in required_fields:
        assert df[field].notna().all(), f"missing required field values in column {field!r}"


def main() -> None:
    df = build()
    _validate(df)

    for r in df.itertuples():
        log_evidence(
            agent="step05_hmm_initial",
            place_id=r.place_id,
            variable="accessibility_from_chennai_central",
            evidence_text=r.justification,
            source=r.source,
            source_url=r.source_url,
        )

    write_sheet("04_HMM_Initial", df)
    print(f"Wrote {len(df)} rows to 04_HMM_Initial (initial_probability sums to {df['initial_probability'].sum(skipna=True):.6f})")


if __name__ == "__main__":
    main()
