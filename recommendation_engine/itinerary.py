"""Formats a Viterbi place sequence into a timed itinerary, with coordinates for
display on a map."""

from dataclasses import dataclass

import pandas as pd

from data_generation.common.workbook import read_sheet
from recommendation_engine.hmm_viterbi import TIME_SLOTS

SLOT_TIMES = {
    "Morning": "09:00 - 12:00",
    "Afternoon": "13:00 - 17:00",
    "Evening": "17:30 - 20:30",
}


@dataclass(frozen=True)
class ItineraryStop:
    slot: str
    time_range: str
    place_id: str
    name: str
    lat: float
    lng: float


def build_itinerary(place_sequence: list[str]) -> list[ItineraryStop]:
    if len(place_sequence) != len(TIME_SLOTS):
        raise ValueError(f"expected {len(TIME_SLOTS)} stops (one per time slot), got {len(place_sequence)}")

    coords = read_sheet("07_Coordinates").set_index("place_id")

    stops = []
    for slot, place_id in zip(TIME_SLOTS, place_sequence):
        row = coords.loc[place_id]
        stops.append(
            ItineraryStop(
                slot=slot,
                time_range=SLOT_TIMES[slot],
                place_id=place_id,
                name=row["name"],
                lat=float(row["lat"]),
                lng=float(row["lng"]),
            )
        )
    return stops


def itinerary_to_dataframe(stops: list[ItineraryStop]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in stops])


def print_itinerary(stops: list[ItineraryStop]) -> None:
    for s in stops:
        print(f"{s.slot} ({s.time_range}): {s.name} [{s.place_id}] @ ({s.lat:.5f}, {s.lng:.5f})")
