"""Builds 03_BN_CPT: P(attribute_value | place) for Age, Budget, Interest, Travel Type
and Weather.

The raw evidence in raw/cpt_research.json was produced by a research pass (web_search
against Wikipedia, official tourism sites and travel guides) that assigned each
(place, variable, state) a raw_score in [0, 1] together with an evidence_text and a
justification that explicitly distinguishes an explicit source claim ("Source states: ...")
from a judgment call drawn from the place's general description ("Inferred from
description: ..."). That research pass never computed a probability itself.

This script is the separate, deterministic normalization pass: for each place and each
variable, it rescales the raw_score values across that variable's states so they sum to
exactly 1. No LLM judgment happens here -- it is plain arithmetic over the raw scores.
"""

import json
from pathlib import Path

import pandas as pd

from data_generation.common.evidence import log_evidence
from data_generation.common.workbook import write_sheet

RAW_RESEARCH_PATH = Path(__file__).resolve().parent / "raw" / "cpt_research.json"

VARIABLE_STATES = {
    "Age": ["Student", "Adult"],
    "Budget": ["Low", "Medium", "High"],
    "Interest": ["History", "Nature", "Spiritual", "Shopping", "Entertainment"],
    "Travel Type": ["Solo", "Friends", "Family"],
    "Weather": ["Sunny", "Rainy"],
}


def load_raw() -> list[dict]:
    with open(RAW_RESEARCH_PATH, encoding="utf-8") as f:
        return json.load(f)


def build() -> pd.DataFrame:
    raw_rows = load_raw()

    by_group: dict[tuple[str, str], list[dict]] = {}
    for r in raw_rows:
        by_group.setdefault((r["place_id"], r["variable"]), []).append(r)

    out_rows = []
    for place_id_variable, group_rows in by_group.items():
        place_id, variable = place_id_variable
        expected_states = set(VARIABLE_STATES[variable])
        got_states = {r["state"] for r in group_rows}
        if got_states != expected_states:
            raise ValueError(f"{place_id}/{variable}: expected states {expected_states}, got {got_states}")

        total = sum(r["raw_score"] for r in group_rows)
        for r in group_rows:
            probability = r["raw_score"] / total if total > 0 else 1.0 / len(group_rows)
            out_rows.append(
                {
                    "place_id": place_id,
                    "place_name": r["place_name"],
                    "variable": variable,
                    "state": r["state"],
                    "probability": probability,
                    "raw_score": r["raw_score"],
                    "evidence_text": r["evidence_text"],
                    "justification": r["justification"],
                    "source_url": r["source_url"],
                }
            )

            log_evidence(
                agent="step04_bn_cpt",
                place_id=place_id,
                variable=variable,
                evidence_text=r["evidence_text"],
                source=r["justification"],
                source_url=r["source_url"],
            )

    df = pd.DataFrame(out_rows)
    df = df.sort_values(["place_id", "variable", "state"]).reset_index(drop=True)
    return df


def main() -> None:
    df = build()

    sums = df.groupby(["place_id", "variable"])["probability"].sum()
    max_error = (sums - 1.0).abs().max()
    assert max_error < 1e-9, f"a (place, variable) group does not sum to 1 (max error {max_error})"

    write_sheet("03_BN_CPT", df)
    print(f"Wrote {len(df)} rows to 03_BN_CPT across {df['place_id'].nunique()} places "
          f"and {df['variable'].nunique()} variables (max group-sum error: {max_error:.2e})")


if __name__ == "__main__":
    main()
