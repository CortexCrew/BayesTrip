"""Builds 05_HMM_Transition: HMM transition probability A[i][j] = P(S_t = place_j |
S_(t-1) = place_i) -- the probability of moving to place_j immediately after visiting
place_i, based on travel accessibility between the two. This is a distinct concept from
02_BN_Prior (P(Place), destination popularity) and 04_HMM_Initial (pi(place),
first-stop accessibility from Chennai Central) -- this script never reads either of
those and only cares about place-to-place movement.

Coordinates come exclusively from 07_Coordinates (Geoapify Geocoding API, the finalized
coordinate source for this project) -- the old OSM Nominatim data is no longer used
anywhere. Distance and travel time for every ordered pair come from a single OSRM table
-service call (common/osrm.py's distance_duration_matrix, added in the 04_HMM_Initial
step and reused here unchanged) rather than 400 individual requests.

Self-transitions (place_i -> place_i) are excluded, matching this project's existing
policy (the prior wide-format implementation set A[i][i] = 0 rather than giving a place
any probability of transitioning to itself) -- so this table has 20 x 19 = 380 rows, one
per ordered pair of DISTINCT places, and each from_id's 19 to_id rows are normalized to
sum to 1 (never all 400 pairs at once).

Formula (deterministic, no LLM judgment), independently per from_id:

    raw_transition_score(i, j) = 1 / (travel_time_min(i, j) + EPSILON)
    transition_probability(i, j) = raw_transition_score(i, j) / sum_k(raw_transition_score(i, k))

where the sum is only over the 19 valid to_places k != i that OSRM could route to.
"""

from datetime import datetime, timezone

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.osrm import distance_duration_matrix
from data_generation.common.places import PLACES
from data_generation.common.workbook import read_sheet, write_sheet

ROUTING_SOURCE = "OSRM public routing API (table service)"
ROUTING_METHOD = "table service, driving profile, single batched 20x20 request (annotations=duration,distance)"
SOURCE_URL = "https://router.project-osrm.org/table/v1/driving/"

EPSILON = 0.01  # minutes; prevents division by zero, negligible next to any real travel time

EXPECTED_PAIR_COUNT = 20 * 19  # self-transitions excluded, per this project's existing policy


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
            f"(place_id(s): {missing_coords['place_id'].tolist()}) -- cannot compute transitions for them."
        )

    canonical_ids = {p["place_id"] for p in PLACES}
    coord_ids = set(coords["place_id"])
    if coord_ids != canonical_ids:
        raise ValueError(f"07_Coordinates place_ids {coord_ids} do not match the canonical list {canonical_ids}")
    if coords["place_id"].duplicated().any():
        raise ValueError(f"07_Coordinates has duplicate place_id values: {coords.loc[coords['place_id'].duplicated(), 'place_id'].tolist()}")
    if len(coords) != 20:
        raise ValueError(f"Expected exactly 20 destinations, found {len(coords)}")

    return coords


def build() -> pd.DataFrame:
    coords = _load_coordinates()
    place_ids = coords["place_id"].tolist()
    names = dict(zip(coords["place_id"], coords["place_name"]))
    lats = dict(zip(coords["place_id"], coords["latitude"]))
    lngs = dict(zip(coords["place_id"], coords["longitude"]))

    points = [{"lat": row.latitude, "lng": row.longitude} for row in coords.itertuples()]
    distances_m, durations_s = distance_duration_matrix(points)

    retrieved_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for i, from_id in enumerate(place_ids):
        pair_raw = {}  # to_id -> (distance_km, travel_time_min, raw_score) for valid pairs
        pair_failed = set()

        for j, to_id in enumerate(place_ids):
            if i == j:
                continue  # self-transitions excluded, per this project's existing policy

            distance_m = distances_m[i][j]
            duration_s = durations_s[i][j]
            if distance_m is None or duration_s is None:
                pair_failed.add(to_id)
                continue

            distance_km = distance_m / 1000.0
            travel_time_min = duration_s / 60.0
            raw_score = 1.0 / (travel_time_min + EPSILON)
            pair_raw[to_id] = (distance_km, travel_time_min, raw_score)

        total_score = sum(v[2] for v in pair_raw.values())

        for to_id in place_ids:
            if to_id == from_id:
                continue

            if to_id in pair_failed:
                rows.append(
                    {
                        "from_id": from_id,
                        "from_place": names[from_id],
                        "to_id": to_id,
                        "to_place": names[to_id],
                        "from_latitude": lats[from_id],
                        "from_longitude": lngs[from_id],
                        "to_latitude": lats[to_id],
                        "to_longitude": lngs[to_id],
                        "distance_km": None,
                        "travel_time_min": None,
                        "raw_transition_score": None,
                        "transition_probability": None,
                        "routing_source": ROUTING_SOURCE,
                        "routing_method": ROUTING_METHOD,
                        "source_url": SOURCE_URL,
                        "retrieved_at": retrieved_at,
                        "justification": (
                            f"OSRM could not find a route from {names[from_id]} to {names[to_id]} "
                            "(no distance/duration returned). No value was fabricated; this pair is "
                            f"excluded from {names[from_id]}'s transition-probability normalization."
                        ),
                        "confidence": "needs_manual_review",
                    }
                )
                continue

            distance_km, travel_time_min, raw_score = pair_raw[to_id]
            probability = raw_score / total_score if total_score > 0 else None
            rows.append(
                {
                    "from_id": from_id,
                    "from_place": names[from_id],
                    "to_id": to_id,
                    "to_place": names[to_id],
                    "from_latitude": lats[from_id],
                    "from_longitude": lngs[from_id],
                    "to_latitude": lats[to_id],
                    "to_longitude": lngs[to_id],
                    "distance_km": round(distance_km, 3),
                    "travel_time_min": round(travel_time_min, 3),
                    "raw_transition_score": raw_score,
                    "transition_probability": probability,
                    "routing_source": ROUTING_SOURCE,
                    "routing_method": ROUTING_METHOD,
                    "source_url": SOURCE_URL,
                    "retrieved_at": retrieved_at,
                    "justification": (
                        f"OSRM reports approximately {travel_time_min:.1f} minutes of travel from "
                        f"{names[from_id]} to {names[to_id]}. The transition raw score is calculated as "
                        f"1/(travel_time_min + {EPSILON}), then normalized against all valid destinations "
                        f"reachable from {names[from_id]}."
                    ),
                    "confidence": "high",
                }
            )

        print(f"{from_id} {names[from_id]}: {len(pair_raw)}/19 valid pairs")

    return pd.DataFrame(rows)


def _validate(df: pd.DataFrame) -> None:
    canonical_ids = {p["place_id"] for p in PLACES}

    assert len(df) == EXPECTED_PAIR_COUNT, f"expected {EXPECTED_PAIR_COUNT} rows (self-transitions excluded), got {len(df)}"
    assert set(df["from_id"]).issubset(canonical_ids), "unknown from_id found"
    assert set(df["to_id"]).issubset(canonical_ids), "unknown to_id found"
    assert set(df["from_id"]) == canonical_ids, "not every canonical place appears as a from_id"
    assert set(df["to_id"]) == canonical_ids, "not every canonical place appears as a to_id"
    assert not (df["from_id"] == df["to_id"]).any(), "a self-transition (from_id == to_id) was found"
    assert not df[["from_id", "to_id"]].duplicated().any(), "duplicate (from_id, to_id) pairs found"

    # Every from_id must have exactly the 19 other places as to_id, no more/fewer.
    counts = df.groupby("from_id")["to_id"].count()
    assert (counts == 19).all(), f"from_id(s) without exactly 19 to_id rows: {counts[counts != 19].to_dict()}"

    valid = df["transition_probability"].notna()
    assert (df.loc[valid, "distance_km"] >= 0).all(), "negative distance found"
    assert (df.loc[valid, "travel_time_min"] >= 0).all(), "negative travel time found"
    assert df.loc[valid, "raw_transition_score"].apply(lambda x: x > 0 and pd.notna(x) and x != float("inf")).all(), "a raw_transition_score is not finite and positive"

    probs = df.loc[valid, "transition_probability"]
    assert ((probs >= 0) & (probs <= 1)).all(), "a transition_probability is outside [0, 1]"

    prob_sums = df.groupby("from_id")["transition_probability"].sum(min_count=1)
    bad_sums = prob_sums[(prob_sums - 1.0).abs() >= 1e-9]
    assert bad_sums.empty, f"from_id(s) whose transition_probability does not sum to 1: {bad_sums.to_dict()}"

    required_fields = [
        "from_id", "from_place", "to_id", "to_place", "from_latitude", "from_longitude",
        "to_latitude", "to_longitude", "routing_source", "routing_method", "source_url",
        "retrieved_at", "justification", "confidence",
    ]
    for field in required_fields:
        assert df[field].notna().all(), f"missing required field values in column {field!r}"

    # Cross-table check: 07_Coordinates is the single source of truth, so every
    # coordinate stored in this table must match it exactly, not any stale source
    # (e.g. the old Nominatim-derived coordinates).
    coords = read_sheet("07_Coordinates").set_index("place_id")
    for prefix, id_col in (("from", "from_id"), ("to", "to_id")):
        merged = df[[id_col, f"{prefix}_latitude", f"{prefix}_longitude"]].drop_duplicates(id_col).set_index(id_col)
        expected = coords.loc[merged.index, ["latitude", "longitude"]]
        lat_mismatch = (merged[f"{prefix}_latitude"] - expected["latitude"]).abs() > 1e-9
        lng_mismatch = (merged[f"{prefix}_longitude"] - expected["longitude"]).abs() > 1e-9
        mismatched = merged.index[lat_mismatch | lng_mismatch].tolist()
        assert not mismatched, f"{prefix}_latitude/{prefix}_longitude do not match 07_Coordinates for: {mismatched}"


def main() -> None:
    df = build()
    _validate(df)

    for r in df.itertuples():
        log_evidence(
            agent="step06_hmm_transition",
            place_id=r.from_id,
            variable=f"transition_to_{r.to_id}",
            evidence_text=r.justification,
            source=r.routing_source,
            source_url=r.source_url,
        )

    write_sheet("05_HMM_Transition", df)
    n_failed = df["transition_probability"].isna().sum()
    print(f"Wrote {len(df)} rows to 05_HMM_Transition ({n_failed} pairs failed routing, flagged needs_manual_review)")


if __name__ == "__main__":
    main()
