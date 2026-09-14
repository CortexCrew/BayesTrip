import pandas as pd
import pytest

from data_generation.common.places import PLACES
from data_generation.step06_hmm_transition import EPSILON, EXPECTED_PAIR_COUNT, ROUTING_METHOD, ROUTING_SOURCE, build, _validate


def _base_row(from_id, to_id, from_lat, from_lng, to_lat, to_lng, travel_time_min, probability, confidence="high"):
    raw_score = 1.0 / (travel_time_min + EPSILON) if travel_time_min is not None else None
    return {
        "from_id": from_id,
        "from_place": f"Place {from_id}",
        "to_id": to_id,
        "to_place": f"Place {to_id}",
        "from_latitude": from_lat,
        "from_longitude": from_lng,
        "to_latitude": to_lat,
        "to_longitude": to_lng,
        "distance_km": (travel_time_min or 0) * 0.5,
        "travel_time_min": travel_time_min,
        "raw_transition_score": raw_score,
        "transition_probability": probability,
        "routing_source": ROUTING_SOURCE,
        "routing_method": ROUTING_METHOD,
        "source_url": "https://router.project-osrm.org/table/v1/driving/",
        "retrieved_at": "2026-01-01T00:00:00+00:00",
        "justification": "test justification",
        "confidence": confidence,
    }


def _make_valid_df():
    place_ids = [p["place_id"] for p in PLACES]
    coord = {pid: (13.0 + i * 0.01, 80.2 + i * 0.01) for i, pid in enumerate(place_ids)}

    rows = []
    for from_id in place_ids:
        others = [pid for pid in place_ids if pid != from_id]
        travel_times = {to_id: 5.0 + idx for idx, to_id in enumerate(others)}
        raw_scores = {to_id: 1.0 / (t + EPSILON) for to_id, t in travel_times.items()}
        total = sum(raw_scores.values())
        for to_id in others:
            from_lat, from_lng = coord[from_id]
            to_lat, to_lng = coord[to_id]
            probability = raw_scores[to_id] / total
            rows.append(_base_row(from_id, to_id, from_lat, from_lng, to_lat, to_lng, travel_times[to_id], probability))
    return pd.DataFrame(rows), coord


def _coords_lookup(monkeypatch, coord):
    import data_generation.step06_hmm_transition as mod

    df = pd.DataFrame(
        [{"place_id": pid, "latitude": lat, "longitude": lng} for pid, (lat, lng) in coord.items()]
    ).set_index("place_id", drop=False)

    monkeypatch.setattr(mod, "read_sheet", lambda name: df.reset_index(drop=True))


def test_valid_dataframe_passes_validation(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    _validate(df)  # should not raise


def test_correct_number_of_transitions():
    df, _ = _make_valid_df()
    assert len(df) == EXPECTED_PAIR_COUNT == 380


def test_canonical_place_ids_only(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    canonical = {p["place_id"] for p in PLACES}
    assert set(df["from_id"]) == canonical
    assert set(df["to_id"]) == canonical


def test_no_self_transitions():
    df, _ = _make_valid_df()
    assert not (df["from_id"] == df["to_id"]).any()


def test_no_duplicate_pairs(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    assert not df[["from_id", "to_id"]].duplicated().any()


def test_probability_range(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    probs = df["transition_probability"]
    assert ((probs >= 0) & (probs <= 1)).all()


def test_per_from_place_normalization(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    sums = df.groupby("from_id")["transition_probability"].sum()
    assert (abs(sums - 1.0) < 1e-9).all()


def test_deterministic_formula_matches_inverse_travel_time():
    df, _ = _make_valid_df()
    row = df.iloc[0]
    expected = 1.0 / (row["travel_time_min"] + EPSILON)
    assert row["raw_transition_score"] == pytest.approx(expected)


def test_validation_rejects_wrong_transition_count(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    df = df.iloc[:-1]
    with pytest.raises(AssertionError, match="expected"):
        _validate(df)


def test_validation_rejects_duplicate_pair(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    dup = df.iloc[[0]].copy()
    df = pd.concat([df, dup], ignore_index=True)
    with pytest.raises(AssertionError):
        _validate(df)


def test_validation_rejects_self_transition(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    bad = df.iloc[0].copy()
    bad["to_id"] = bad["from_id"]
    df = pd.concat([df.iloc[1:], pd.DataFrame([bad])], ignore_index=True)
    with pytest.raises(AssertionError, match="self-transition"):
        _validate(df)


def test_validation_rejects_bad_probability_sum(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    df.loc[df["from_id"] == df["from_id"].iloc[0], "transition_probability"] *= 2
    with pytest.raises(AssertionError, match="does not sum to 1"):
        _validate(df)


def test_validation_rejects_coordinate_mismatch_with_07_coordinates(monkeypatch):
    df, coord = _make_valid_df()
    _coords_lookup(monkeypatch, coord)
    df.loc[0, "from_latitude"] = df.loc[0, "from_latitude"] + 5.0  # diverge from 07_Coordinates
    with pytest.raises(AssertionError, match="do not match 07_Coordinates"):
        _validate(df)


def test_validation_handles_a_failed_routing_pair_without_fabricating(monkeypatch):
    # A failed pair (transition_probability=None) should not block validation as long
    # as the remaining 18 valid pairs for that from_id still sum to 1.
    df, coord = _make_valid_df()
    place_ids = [p["place_id"] for p in PLACES]
    from_id, failed_to_id = place_ids[0], place_ids[1]
    mask = (df["from_id"] == from_id) & (df["to_id"] == failed_to_id)
    remaining = (df["from_id"] == from_id) & (df["to_id"] != failed_to_id)

    df.loc[mask, ["distance_km", "travel_time_min", "raw_transition_score", "transition_probability"]] = None
    df.loc[mask, "confidence"] = "needs_manual_review"
    # Renormalize the remaining 18 pairs for that from_id to sum to 1 on their own.
    remaining_total = df.loc[remaining, "raw_transition_score"].sum()
    df.loc[remaining, "transition_probability"] = df.loc[remaining, "raw_transition_score"] / remaining_total

    _coords_lookup(monkeypatch, coord)
    _validate(df)  # should not raise -- failed pair is None, not fabricated, and excluded from the sum check


def test_build_marks_a_failed_osrm_pair_as_needs_manual_review_without_fabricating(monkeypatch):
    import data_generation.step06_hmm_transition as mod

    place_ids = [p["place_id"] for p in PLACES]
    coords_df = pd.DataFrame(
        {
            "place_id": place_ids,
            "place_name": [f"Place {pid}" for pid in place_ids],
            "latitude": [13.0 + i * 0.01 for i in range(20)],
            "longitude": [80.2 + i * 0.01 for i in range(20)],
            "source": ["Geoapify Geocoding API"] * 20,
        }
    )
    monkeypatch.setattr(mod, "read_sheet", lambda name: coords_df)

    n = len(place_ids)
    distances = [[0 if i == j else 1000.0 * (i + j + 1) for j in range(n)] for i in range(n)]
    durations = [[0 if i == j else 60.0 * (i + j + 1) for j in range(n)] for i in range(n)]
    # Simulate OSRM being unable to route from place 0 to place 1.
    distances[0][1] = None
    durations[0][1] = None
    monkeypatch.setattr(mod, "distance_duration_matrix", lambda points: (distances, durations))

    df = build()

    failed_row = df[(df["from_id"] == place_ids[0]) & (df["to_id"] == place_ids[1])].iloc[0]
    assert pd.isna(failed_row["transition_probability"])
    assert pd.isna(failed_row["distance_km"])
    assert failed_row["confidence"] == "needs_manual_review"

    # The other 18 valid pairs from place_ids[0] should still sum to 1 on their own.
    remaining = df[(df["from_id"] == place_ids[0]) & (df["to_id"] != place_ids[1])]
    assert len(remaining) == 18
    assert remaining["transition_probability"].sum() == pytest.approx(1.0)
