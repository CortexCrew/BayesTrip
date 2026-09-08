"""Bayesian posterior scoring over places given visitor evidence.

Score(Pi) is proportional to P(Pi) * prod_k P(Ek | Pi), where Ek ranges over the
observed evidence variables (Age, Budget, Interest, Travel Type, Weather). The raw
scores are normalized across all places to form a proper posterior, and the Top-5
places by posterior probability are selected for the HMM stage.
"""

from dataclasses import dataclass

import pandas as pd

from data_generation.common.workbook import read_sheet

EVIDENCE_VARIABLES = ["Age", "Budget", "Interest", "Travel Type", "Weather"]


@dataclass(frozen=True)
class Evidence:
    age: str
    budget: str
    interest: str
    travel_type: str
    weather: str

    def as_dict(self) -> dict:
        return {
            "Age": self.age,
            "Budget": self.budget,
            "Interest": self.interest,
            "Travel Type": self.travel_type,
            "Weather": self.weather,
        }


def _load_prior() -> pd.DataFrame:
    return read_sheet("02_BN_Prior")


def _load_cpt() -> pd.DataFrame:
    return read_sheet("03_BN_CPT")


def score_places(evidence: Evidence, prior: pd.DataFrame | None = None, cpt: pd.DataFrame | None = None) -> pd.DataFrame:
    """Returns a DataFrame with columns [place_id, name, posterior], sorted descending
    by posterior, summing to 1 across all places."""
    prior = _load_prior() if prior is None else prior
    cpt = _load_cpt() if cpt is None else cpt

    evidence_dict = evidence.as_dict()
    for variable, state in evidence_dict.items():
        valid_states = set(cpt.loc[cpt["variable"] == variable, "state"])
        if state not in valid_states:
            raise ValueError(f"Unknown state {state!r} for variable {variable!r}; expected one of {sorted(valid_states)}")

    scores = prior.set_index("place_id")["probability"].astype(float).copy()
    names = prior.set_index("place_id")["name"] if "name" in prior.columns else prior.set_index("place_id")["place_name"]

    for variable, state in evidence_dict.items():
        likelihood = cpt[(cpt["variable"] == variable) & (cpt["state"] == state)].set_index("place_id")["probability"]
        scores = scores * likelihood.reindex(scores.index).astype(float)

    total = scores.sum()
    posterior = scores / total

    result = pd.DataFrame({"place_id": posterior.index, "name": names.reindex(posterior.index).values, "posterior": posterior.values})
    return result.sort_values("posterior", ascending=False).reset_index(drop=True)


def top_n(evidence: Evidence, n: int = 5, prior: pd.DataFrame | None = None, cpt: pd.DataFrame | None = None) -> pd.DataFrame:
    return score_places(evidence, prior=prior, cpt=cpt).head(n).reset_index(drop=True)
