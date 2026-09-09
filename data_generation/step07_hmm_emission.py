"""Builds 06_HMM_Emission: per-place suitability for Morning/Afternoon/Evening.

Time slots are fixed as Morning 06:00-12:00, Afternoon 12:00-17:00, Evening 17:00-21:00.
Opening hours per place were researched (raw/opening_hours_research.json, free text with
sources) and hand-extracted into structured daily intervals (raw/opening_hours.json).
This script is the deterministic scoring pass over those structured intervals:

  - slot fully covered by an open interval  -> 1.0 (fully open)
  - slot has partial overlap with an open interval -> 0.5 (partially open)
  - slot has no overlap at all -> 0.02 (closed floor; never a hard 0, so Viterbi can
    still transition through this state instead of permanently zeroing it out)

Scores are then normalized per place across the 3 slots to sum to 1.
"""

import json
from pathlib import Path

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.workbook import write_sheet

RAW_STRUCTURED_PATH = Path(__file__).resolve().parent / "raw" / "opening_hours.json"
RAW_RESEARCH_PATH = Path(__file__).resolve().parent / "raw" / "opening_hours_research.json"

SLOTS = {"Morning": (6, 12), "Afternoon": (12, 17), "Evening": (17, 21)}

FULL_SCORE = 1.0
PARTIAL_SCORE = 0.5
CLOSED_FLOOR = 0.02


def _overlap_hours(interval: tuple[float, float], slot: tuple[float, float]) -> float:
    return max(0.0, min(interval[1], slot[1]) - max(interval[0], slot[0]))


def _slot_fraction_open(intervals: list[list[float]], slot: tuple[float, float]) -> float:
    slot_duration = slot[1] - slot[0]
    covered = sum(_overlap_hours(tuple(iv), slot) for iv in intervals)
    return covered / slot_duration


def build() -> pd.DataFrame:
    with open(RAW_STRUCTURED_PATH, encoding="utf-8") as f:
        structured = json.load(f)
    with open(RAW_RESEARCH_PATH, encoding="utf-8") as f:
        research_by_place = {r["place_id"]: r for r in json.load(f)}

    place_ids = [pid for pid in structured if not pid.startswith("_")]

    rows = []
    for pid in place_ids:
        entry = structured[pid]
        intervals = entry["intervals"]
        research = research_by_place[pid]

        raw_scores = {}
        statuses = {}
        for slot_name, slot_range in SLOTS.items():
            frac = _slot_fraction_open(intervals, slot_range)
            if frac >= 0.999:
                raw_scores[slot_name] = FULL_SCORE
                statuses[slot_name] = "fully open"
            elif frac <= 0.001:
                raw_scores[slot_name] = CLOSED_FLOOR
                statuses[slot_name] = "closed"
            else:
                raw_scores[slot_name] = PARTIAL_SCORE
                statuses[slot_name] = "partially open"

        total = sum(raw_scores.values())
        for slot_name in SLOTS:
            probability = raw_scores[slot_name] / total
            rows.append(
                {
                    "place_id": pid,
                    "name": entry["name"],
                    "slot": slot_name,
                    "status": statuses[slot_name],
                    "raw_score": raw_scores[slot_name],
                    "probability": probability,
                    "opening_hours_text": research["opening_hours_text"],
                    "source": research["source"],
                    "source_url": research["source_url"],
                }
            )

        print(f"{pid} {entry['name']}: {statuses}")

    return pd.DataFrame(rows)


def main() -> None:
    df = build()
    sums = df.groupby("place_id")["probability"].sum()
    max_error = (sums - 1.0).abs().max()
    assert max_error < 1e-9, f"a place's emission scores do not sum to 1 (max error {max_error})"

    for pid, group in df.groupby("place_id"):
        first = group.iloc[0]
        log_evidence(
            agent="step07_hmm_emission",
            place_id=pid,
            variable="opening_hours",
            evidence_text=first["opening_hours_text"],
            source=first["source"],
            source_url=first["source_url"],
        )

    write_sheet("06_HMM_Emission", df)
    print(f"Wrote {len(df)} rows to 06_HMM_Emission (max per-place sum error: {max_error:.2e})")


if __name__ == "__main__":
    main()
