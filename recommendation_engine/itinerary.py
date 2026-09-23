"""Formats a Viterbi place sequence into a timed itinerary, with coordinates for
display on a map."""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from data_generation.common.workbook import read_sheet
from recommendation_engine.hmm_viterbi import _position_time_slots

SLOT_TIMES = {
    "Morning": "09:00 - 12:00",
    "Afternoon": "13:00 - 17:00",
    "Evening": "17:30 - 20:30",
}


def _sub_range(time_range: str, ordinal: int, total: int) -> str:
    """Splits a slot's base time_range into `total` equal sub-windows and returns the
    `ordinal`-th (0-based) one -- used when a slot (e.g. "Morning") is reused for more
    than one itinerary position, so each stop still gets a distinct, non-overlapping
    time window without inventing any new slot data."""
    if total == 1:
        return time_range
    start_str, end_str = (s.strip() for s in time_range.split("-"))
    start, end = datetime.strptime(start_str, "%H:%M"), datetime.strptime(end_str, "%H:%M")
    step = (end - start) / total
    sub_start = start + step * ordinal
    sub_end = start + step * (ordinal + 1)
    return f"{sub_start.strftime('%H:%M')} - {sub_end.strftime('%H:%M')}"


@dataclass(frozen=True)
class ItineraryStop:
    slot: str
    time_range: str
    place_id: str
    name: str
    lat: float
    lng: float


def build_itinerary(place_sequence: list[str]) -> list[ItineraryStop]:
    # One position per place in the sequence (a unique-visitation itinerary -- see
    # hmm_viterbi.decode_sequence), mapped onto the existing Morning/Afternoon/Evening
    # emission slots the same way decode_sequence does, so the displayed slot matches
    # the one Viterbi actually scored that stop against.
    position_slots = _position_time_slots(len(place_sequence))

    coords = read_sheet("07_Coordinates").set_index("place_id")

    slot_counts = Counter(position_slots)
    slot_seen = Counter()

    stops = []
    for slot, place_id in zip(position_slots, place_sequence):
        ordinal = slot_seen[slot]
        slot_seen[slot] += 1
        time_range = _sub_range(SLOT_TIMES[slot], ordinal, slot_counts[slot])

        row = coords.loc[place_id]
        stops.append(
            ItineraryStop(
                slot=slot,
                time_range=time_range,
                place_id=place_id,
                name=row["place_name"],
                lat=float(row["latitude"]),
                lng=float(row["longitude"]),
            )
        )
    return stops


def itinerary_to_dataframe(stops: list[ItineraryStop]) -> pd.DataFrame:
    return pd.DataFrame([s.__dict__ for s in stops])


def print_itinerary(stops: list[ItineraryStop]) -> None:
    for s in stops:
        print(f"{s.slot} ({s.time_range}): {s.name} [{s.place_id}] @ ({s.lat:.5f}, {s.lng:.5f})")
