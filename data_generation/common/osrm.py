"""Thin wrapper around the public OSRM table service (many-to-many travel times).

OSRM's public demo server caps table requests at 100 total coordinates, which is
comfortably above what this project needs (21 points for the 20x20 transition
matrix + Chennai Central).
"""

from data_generation.common.http import get

OSRM_TABLE_URL = "https://router.project-osrm.org/table/v1/driving/{coords}"

CHENNAI_CENTRAL = {"name": "Chennai Central Railway Station", "lat": 13.0825901, "lng": 80.2763077}


def duration_matrix(points: list[dict]) -> list[list[float]]:
    """points: list of {"lat": float, "lng": float}. Returns durations in seconds,
    matrix[i][j] = travel time from points[i] to points[j]."""
    coords = ";".join(f"{p['lng']},{p['lat']}" for p in points)
    url = OSRM_TABLE_URL.format(coords=coords)
    response = get(url, params={"annotations": "duration"})
    data = response.json()
    if data.get("code") != "Ok":
        raise ValueError(f"OSRM table request failed: {data}")
    return data["durations"]


def distance_duration_matrix(points: list[dict]) -> tuple[list[list[float]], list[list[float]]]:
    """Same as duration_matrix, but also returns road distances. points: list of
    {"lat": float, "lng": float}. Returns (distances_meters, durations_seconds), each
    matrix[i][j] = value from points[i] to points[j]. A cell is None where OSRM
    couldn't find a route between that pair."""
    coords = ";".join(f"{p['lng']},{p['lat']}" for p in points)
    url = OSRM_TABLE_URL.format(coords=coords)
    response = get(url, params={"annotations": "duration,distance"})
    data = response.json()
    if data.get("code") != "Ok":
        raise ValueError(f"OSRM table request failed: {data}")
    return data["distances"], data["durations"]
