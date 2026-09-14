import pandas as pd
import pytest

from data_generation.common.osrm import CHENNAI_CENTRAL
from data_generation.common.places import PLACES
from data_generation.step05_hmm_initial import DISTANCE_METHOD, EPSILON, _validate


def _make_valid_df():
    rows = []
    for i, p in enumerate(PLACES):
        travel_time_min = 5.0 + i  # arbitrary but distinct, all positive
        raw_score = 1.0 / (travel_time_min + EPSILON)
        rows.append(
            {
                "place_id": p["place_id"],
                "place_name": p["name"],
                "start_location": CHENNAI_CENTRAL["name"],
                "start_latitude": CHENNAI_CENTRAL["lat"],
                "start_longitude": CHENNAI_CENTRAL["lng"],
                "place_latitude": 13.0 + i * 0.01,
                "place_longitude": 80.2 + i * 0.01,
                "distance_km": 3.0 + i,
                "travel_time_min": travel_time_min,
                "raw_accessibility_score": raw_score,
                "distance_method": DISTANCE_METHOD,
                "source": "OSRM public routing API (table service)",
                "source_url": "https://router.project-osrm.org/table/v1/driving/",
                "retrieved_at": "2026-01-01T00:00:00+00:00",
                "justification": "test justification",
                "confidence": "high",
            }
        )
    df = pd.DataFrame(rows)
    total = df["raw_accessibility_score"].sum()
    df["initial_probability"] = df["raw_accessibility_score"] / total
    return df


def test_valid_dataframe_passes_validation():
    _validate(_make_valid_df())  # should not raise


def test_formula_matches_inverse_travel_time():
    df = _make_valid_df()
    row = df.iloc[0]
    expected_raw = 1.0 / (row["travel_time_min"] + EPSILON)
    assert row["raw_accessibility_score"] == pytest.approx(expected_raw)


def test_probabilities_sum_to_one():
    df = _make_valid_df()
    assert df["initial_probability"].sum() == pytest.approx(1.0)


def test_validation_rejects_wrong_place_count():
    df = _make_valid_df().iloc[:19].copy()
    with pytest.raises(AssertionError, match="exactly 20"):
        _validate(df)


def test_validation_rejects_duplicate_place_id():
    df = _make_valid_df().iloc[:19]
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)  # duplicate P01, still 20 rows, canonical set incomplete
    with pytest.raises(AssertionError):
        _validate(df)


def test_validation_rejects_wrong_start_location():
    df = _make_valid_df()
    df.loc[0, "start_location"] = "Somewhere Else"
    with pytest.raises(AssertionError, match="start_location"):
        _validate(df)


def test_validation_rejects_bad_probability_sum():
    df = _make_valid_df()
    df["initial_probability"] = df["initial_probability"] * 2
    with pytest.raises(AssertionError, match="does not sum to 1"):
        _validate(df)


def test_validation_rejects_missing_required_field():
    df = _make_valid_df()
    df.loc[0, "justification"] = None
    with pytest.raises(AssertionError, match="missing required field"):
        _validate(df)


def test_epsilon_is_small_and_positive():
    assert 0 < EPSILON < 1
