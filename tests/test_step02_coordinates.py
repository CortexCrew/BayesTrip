from data_generation.common.osrm import CHENNAI_CENTRAL
from data_generation.step02_coordinates import MAX_DISTANCE_FROM_CENTER_KM, _haversine_km, _select_best


def test_haversine_zero_distance():
    assert _haversine_km(13.0, 80.0, 13.0, 80.0) == 0.0


def test_haversine_known_distance_is_reasonable():
    # Chennai Central to Marina Beach is a short hop, well under 5km.
    d = _haversine_km(CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"], 13.0533, 80.2833)
    assert 0 < d < 5


def test_select_best_prefers_higher_confidence():
    near_lat, near_lon = CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"]
    results = [
        {"lat": near_lat, "lon": near_lon, "rank": {"confidence": 0.5}, "place_id": "low"},
        {"lat": near_lat, "lon": near_lon, "rank": {"confidence": 0.9}, "place_id": "high"},
    ]
    picked = _select_best(results)
    assert picked is not None
    assert picked["result"]["place_id"] == "high"


def test_select_best_rejects_results_far_from_chennai():
    # Roughly Bangalore, ~290km from Chennai -- well outside the validation radius.
    far_result = {"lat": 12.9716, "lon": 77.5946, "rank": {"confidence": 0.99}, "place_id": "far"}
    picked = _select_best([far_result])
    assert picked is None


def test_select_best_returns_none_for_empty_results():
    assert _select_best([]) is None


def test_select_best_breaks_confidence_ties_by_distance():
    near_lat, near_lon = CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"]
    farther = {"lat": near_lat + 0.2, "lon": near_lon, "rank": {"confidence": 0.8}, "place_id": "farther"}
    closer = {"lat": near_lat + 0.01, "lon": near_lon, "rank": {"confidence": 0.8}, "place_id": "closer"}
    picked = _select_best([farther, closer])
    assert picked["result"]["place_id"] == "closer"


def test_max_distance_threshold_is_positive():
    assert MAX_DISTANCE_FROM_CENTER_KM > 0
