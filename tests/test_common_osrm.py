from unittest.mock import MagicMock

from data_generation.common.osrm import distance_duration_matrix, duration_matrix


def _mock_response(json_payload):
    response = MagicMock()
    response.json.return_value = json_payload
    return response


def test_duration_matrix_parses_ok_response(monkeypatch):
    import data_generation.common.osrm as mod

    monkeypatch.setattr(mod, "get", lambda url, params=None: _mock_response({"code": "Ok", "durations": [[0, 100], [100, 0]]}))
    result = duration_matrix([{"lat": 1, "lng": 1}, {"lat": 2, "lng": 2}])
    assert result == [[0, 100], [100, 0]]


def test_distance_duration_matrix_parses_both_annotations(monkeypatch):
    import data_generation.common.osrm as mod

    payload = {"code": "Ok", "distances": [[0, 5000], [5000, 0]], "durations": [[0, 300], [300, 0]]}
    monkeypatch.setattr(mod, "get", lambda url, params=None: _mock_response(payload))
    distances, durations = distance_duration_matrix([{"lat": 1, "lng": 1}, {"lat": 2, "lng": 2}])
    assert distances == [[0, 5000], [5000, 0]]
    assert durations == [[0, 300], [300, 0]]


def test_distance_duration_matrix_preserves_null_cells_for_failed_routes(monkeypatch):
    import data_generation.common.osrm as mod

    # OSRM returns null for a pair it can't route between, rather than omitting it.
    payload = {"code": "Ok", "distances": [[0, None], [None, 0]], "durations": [[0, None], [None, 0]]}
    monkeypatch.setattr(mod, "get", lambda url, params=None: _mock_response(payload))
    distances, durations = distance_duration_matrix([{"lat": 1, "lng": 1}, {"lat": 2, "lng": 2}])
    assert distances[0][1] is None
    assert durations[0][1] is None


def test_duration_matrix_raises_on_non_ok_code(monkeypatch):
    import data_generation.common.osrm as mod
    import pytest

    monkeypatch.setattr(mod, "get", lambda url, params=None: _mock_response({"code": "InvalidQuery"}))
    with pytest.raises(ValueError, match="OSRM table request failed"):
        duration_matrix([{"lat": 1, "lng": 1}])
