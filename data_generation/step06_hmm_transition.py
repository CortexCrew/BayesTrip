"""Builds 05_HMM_Transition: pairwise travel-time matrix for all 20x20 place pairs via OSRM.

Formula: A_ij = 1 / travel_time_seconds(place_i -> place_j) for i != j, A_ii = 0,
each row normalized to sum to 1. Deterministic, no LLM judgment.
"""

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.osrm import duration_matrix
from data_generation.common.workbook import read_sheet, write_sheet


def build() -> pd.DataFrame:
    coords_df = read_sheet("07_Coordinates")
    place_ids = coords_df["place_id"].tolist()
    names = dict(zip(coords_df["place_id"], coords_df["name"]))
    points = [{"lat": row.lat, "lng": row.lng} for row in coords_df.itertuples()]

    # OSRM's public demo server caps table requests at 100 total coordinates;
    # 20x20 is well within that, so this is a single call rather than a batched loop.
    durations = duration_matrix(points)

    rows = []
    for i, pid_i in enumerate(place_ids):
        raw_scores = []
        for j, pid_j in enumerate(place_ids):
            if i == j:
                raw_scores.append(0.0)
                continue
            t = durations[i][j]
            raw_scores.append(1.0 / t if t and t > 0 else 0.0)

        total = sum(raw_scores)
        row = {"from_place_id": pid_i, "from_name": names[pid_i]}
        for j, pid_j in enumerate(place_ids):
            row[pid_j] = raw_scores[j] / total if total > 0 else 0.0
        rows.append(row)
        print(f"{pid_i} {names[pid_i]}: row done")

    return pd.DataFrame(rows)


def main() -> None:
    df = build()
    row_sums = df[[c for c in df.columns if c not in ("from_place_id", "from_name")]].sum(axis=1)
    assert (row_sums - 1.0).abs().max() < 1e-9, "a transition row does not sum to 1"

    for r in df.itertuples():
        log_evidence(
            agent="step06_hmm_transition",
            place_id=r.from_place_id,
            variable="transition_row",
            evidence_text=f"OSRM driving durations from {r.from_place_id} to all other 19 places, row normalized to sum to 1",
            source="OSRM public routing API (table service)",
            source_url="https://router.project-osrm.org/table/v1/driving/",
        )

    write_sheet("05_HMM_Transition", df)
    print(f"Wrote {len(df)} rows to 05_HMM_Transition (max row-sum error: {(row_sums - 1.0).abs().max():.2e})")


if __name__ == "__main__":
    main()
