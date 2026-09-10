"""Builds 02_BN_Prior: P(Place) from researched popularity evidence.

OpenTripMap (originally planned for this) is blocked, and isn't a rating/review source
anyway -- popularity evidence here comes from a web-research pass (raw/popularity_research.json):
for each place, rating and review_count were looked up via normal web search, preferring
Tripadvisor's publicly visible numbers where a normal search/page-load surfaces them (no
scraping, no bypassing access restrictions), falling back to another reliable source
(recorded explicitly) when Tripadvisor isn't accessible that way. Places with no findable
rating/review_count anywhere have both left null rather than invented.

This script is the separate, deterministic scoring pass over that raw evidence -- see
DESIGN.md for the exact formula and its rationale. No LLM judgment happens here.
"""

import json
from math import log
from pathlib import Path

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.workbook import write_sheet

RAW_RESEARCH_PATH = Path(__file__).resolve().parent / "raw" / "popularity_research.json"

FLOOR_SCORE = 1.0  # applied only when neither rating nor review_count is known for a place


def load_raw() -> list[dict]:
    with open(RAW_RESEARCH_PATH, encoding="utf-8") as f:
        return json.load(f)


def _popularity_score(rating: float | None, review_count: int | None) -> tuple[float, str]:
    if rating is not None and review_count is not None:
        score = rating * log(review_count + 1)
        return score, f"rating({rating}) * ln(review_count({review_count}) + 1) = {score:.4f}"
    if rating is not None:
        return rating, f"rating only, no review_count evidence: score = rating = {rating}"
    return FLOOR_SCORE, f"no rating or review_count evidence found: floor score = {FLOOR_SCORE}"


def build() -> pd.DataFrame:
    raw_rows = load_raw()

    rows = []
    for r in raw_rows:
        score, score_note = _popularity_score(r["rating"], r["review_count"])
        rows.append(
            {
                "place_id": r["place_id"],
                "place_name": r["place_name"],
                "rating": r["rating"],
                "review_count": r["review_count"],
                "popularity_score": score,
                "score_formula": score_note,
                "justification": r["justification"],
                "evidence_text": r["evidence_text"],
                "source": r["source"],
                "source_url": r["source_url"],
                "confidence": r["confidence"],
            }
        )

    df = pd.DataFrame(rows)
    total = df["popularity_score"].sum()
    df["prior_probability"] = df["popularity_score"] / total
    return df.sort_values("place_id").reset_index(drop=True)


def main() -> None:
    df = build()
    assert abs(df["prior_probability"].sum() - 1.0) < 1e-9, "prior_probability does not sum to 1"

    for r in df.itertuples():
        log_evidence(
            agent="step03_bn_prior",
            place_id=r.place_id,
            variable="popularity",
            evidence_text=r.evidence_text,
            source=r.source,
            source_url=r.source_url,
        )

    output_columns = [
        "place_id",
        "place_name",
        "rating",
        "review_count",
        "popularity_score",
        "prior_probability",
        "justification",
        "source",
        "source_url",
        "confidence",
    ]
    write_sheet("02_BN_Prior", df[output_columns].assign(retrieved_at=pd.Timestamp.now(tz="UTC").isoformat()))
    print(f"Wrote {len(df)} rows to 02_BN_Prior (sums to {df['prior_probability'].sum():.6f})")


if __name__ == "__main__":
    main()
