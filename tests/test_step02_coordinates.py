from data_generation.common.osrm import CHENNAI_CENTRAL
from data_generation.step02_coordinates import (
    MAX_DISTANCE_FROM_CENTER_KM,
    MIN_CONFIDENCE,
    _category_word,
    _haversine_km,
    _select_best,
)


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


def test_select_best_rejects_geoapify_city_level_fallback_match():
    # Regression test: Geoapify falls back to a low-confidence city-level match
    # (observed confidence ~0.25, match_type "match_by_city_or_disrict") when it
    # can't resolve the actual named POI -- e.g. querying "San Thome Basilica"
    # once returned plain "Chennai" city center at confidence 0.25. This must be
    # rejected rather than silently accepted as the place's coordinate.
    city_level_fallback = {
        "lat": CHENNAI_CENTRAL["lat"],
        "lon": CHENNAI_CENTRAL["lng"],
        "name": "Chennai",
        "result_type": "city",
        "rank": {"confidence": 0.25, "match_type": "match_by_city_or_disrict"},
    }
    assert _select_best([city_level_fallback]) is None


def test_min_confidence_is_between_zero_and_one():
    assert 0 < MIN_CONFIDENCE < 1


def test_category_word_extracts_the_type_noun():
    assert _category_word("Vivekananda House") == "house"
    assert _category_word("San Thome Basilica") == "basilica"
    assert _category_word("Arignar Anna Zoological Park (Vandalur Zoo)") == "park"
    assert _category_word("Government Museum, Chennai") == "museum"


def test_select_best_rejects_a_similarly_named_wrong_poi():
    # Regression test: Geoapify matched "Vivekananda House" to the real but unrelated
    # "Vivekananda College" at confidence 1.0 (full_match) -- high confidence alone
    # doesn't catch this, since it's a genuine full-string match, just to the wrong
    # nearby place. The category-word check (here: "house" not present in "college")
    # must reject it.
    near_lat, near_lon = CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"]
    wrong_poi = {
        "lat": near_lat,
        "lon": near_lon,
        "name": None,
        "formatted": "Vivekananda College, Ward 119, Chennai - 600086, TN, India",
        "rank": {"confidence": 1.0},
    }
    assert _select_best([wrong_poi], place_name="Vivekananda House") is None


def test_select_best_accepts_a_correctly_named_poi_with_category_word():
    near_lat, near_lon = CHENNAI_CENTRAL["lat"], CHENNAI_CENTRAL["lng"]
    correct_poi = {
        "lat": near_lat,
        "lon": near_lon,
        "name": "St. Thomas Cathedral Basilica",
        "formatted": "St. Thomas Cathedral Basilica, Santhome, Chennai, TN, India",
        "rank": {"confidence": 0.9},
    }
    picked = _select_best([correct_poi], place_name="San Thome Basilica")
    assert picked is not None
    assert picked["result"] is correct_poi
