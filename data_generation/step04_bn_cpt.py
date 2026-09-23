
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

    df = pd.DataFrame(out_rows)
    df = df.sort_values(["place_id", "variable", "state"]).reset_index(drop=True)
    return df


def main() -> None:
    df = build()

    sums = df.groupby(["place_id", "variable"])["probability"].sum()
    max_error = (sums - 1.0).abs().max()
    assert max_error < 1e-9, f"a (place, variable) group does not sum to 1 (max error {max_error})"

    for r in df.itertuples():
        log_evidence(
            agent="step04_bn_cpt",
            place_id=r.place_id,
            variable=r.variable,
            evidence_text=r.evidence_text,
            source=r.justification,
            source_url=r.source_url,
        )

    write_sheet("03_BN_CPT", df)
    print(f"Wrote {len(df)} rows to 03_BN_CPT across {df['place_id'].nunique()} places "
          f"and {df['variable'].nunique()} variables (max group-sum error: {max_error:.2e})")


if __name__ == "__main__":
    main()
