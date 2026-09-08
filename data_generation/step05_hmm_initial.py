"""Builds 04_HMM_Initial: pi_i from Chennai Central to each place via OSRM travel time.

Formula: score_i = 1 / travel_time_seconds(Chennai Central -> place_i), then normalized
to sum to 1 across all 20 places. Deterministic, no LLM judgment.
"""

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.osrm import CHENNAI_CENTRAL, duration_matrix
from data_generation.common.workbook import read_sheet, write_sheet


def build() -> pd.DataFrame:
    coords_df = read_sheet("07_Coordinates")
    points = [{"lat": CHENNAI_CENTRAL["lat"], "lng": CHENNAI_CENTRAL["lng"]}]
    points += [{"lat": row.lat, "lng": row.lng} for row in coords_df.itertuples()]

    durations = duration_matrix(points)
    from_central = durations[0][1:]  # row 0 = Chennai Central, columns 1..N = places

    scores = [1.0 / t if t and t > 0 else 0.0 for t in from_central]
    total = sum(scores)
    pis = [s / total for s in scores]

    rows = []
    for row, travel_time, score, pi in zip(coords_df.itertuples(), from_central, scores, pis):
        rows.append(
            {
                "place_id": row.place_id,
                "name": row.name,
                "travel_time_seconds": round(travel_time, 1),
                "raw_score": score,
                "pi": pi,
            }
        )
        log_evidence(
            agent="step05_hmm_initial",
            place_id=row.place_id,
            variable="travel_time_from_chennai_central",
            evidence_text=f"OSRM driving duration = {travel_time:.1f}s from Chennai Central Railway Station",
            source="OSRM public routing API (table service)",
            source_url="https://router.project-osrm.org/table/v1/driving/",
        )
        print(f"{row.place_id} {row.name}: {travel_time:.0f}s -> pi={pi:.4f}")

    return pd.DataFrame(rows)


def main() -> None:
    df = build()
    assert abs(df["pi"].sum() - 1.0) < 1e-9, "pi does not sum to 1"
    write_sheet("04_HMM_Initial", df)
    print(f"Wrote {len(df)} rows to 04_HMM_Initial (pi sums to {df['pi'].sum():.6f})")


if __name__ == "__main__":
    main()
