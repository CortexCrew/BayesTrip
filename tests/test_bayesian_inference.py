import pandas as pd
import pytest

from recommendation_engine.bayesian_inference import Evidence, score_places, top_n

PRIOR = pd.DataFrame(
    {
        "place_id": ["A", "B", "C"],
        "name": ["Alpha", "Beta", "Gamma"],
        "probability": [0.5, 0.3, 0.2],
    }
)

CPT = pd.DataFrame(
    [
        # variable, state, place_id, probability -- Age
        ("Age", "Student", "A", 0.8), ("Age", "Student", "B", 0.1), ("Age", "Student", "C", 0.1),
        ("Age", "Adult", "A", 0.2), ("Age", "Adult", "B", 0.5), ("Age", "Adult", "C", 0.3),
        # Budget
        ("Budget", "Low", "A", 0.6), ("Budget", "Low", "B", 0.2), ("Budget", "Low", "C", 0.2),
        ("Budget", "Medium", "A", 0.3), ("Budget", "Medium", "B", 0.4), ("Budget", "Medium", "C", 0.3),
        ("Budget", "High", "A", 0.1), ("Budget", "High", "B", 0.4), ("Budget", "High", "C", 0.5),
        # Interest
        ("Interest", "History", "A", 0.7), ("Interest", "History", "B", 0.1), ("Interest", "History", "C", 0.2),
        ("Interest", "Nature", "A", 0.1), ("Interest", "Nature", "B", 0.7), ("Interest", "Nature", "C", 0.2),
        ("Interest", "Spiritual", "A", 0.1), ("Interest", "Spiritual", "B", 0.1), ("Interest", "Spiritual", "C", 0.8),
        ("Interest", "Shopping", "A", 0.3), ("Interest", "Shopping", "B", 0.3), ("Interest", "Shopping", "C", 0.4),
        ("Interest", "Entertainment", "A", 0.3), ("Interest", "Entertainment", "B", 0.3), ("Interest", "Entertainment", "C", 0.4),
        # Travel Type
        ("Travel Type", "Solo", "A", 0.5), ("Travel Type", "Solo", "B", 0.3), ("Travel Type", "Solo", "C", 0.2),
        ("Travel Type", "Friends", "A", 0.3), ("Travel Type", "Friends", "B", 0.4), ("Travel Type", "Friends", "C", 0.3),
        ("Travel Type", "Family", "A", 0.2), ("Travel Type", "Family", "B", 0.3), ("Travel Type", "Family", "C", 0.5),
        # Weather
        ("Weather", "Sunny", "A", 0.6), ("Weather", "Sunny", "B", 0.5), ("Weather", "Sunny", "C", 0.4),
        ("Weather", "Rainy", "A", 0.4), ("Weather", "Rainy", "B", 0.5), ("Weather", "Rainy", "C", 0.6),
    ],
    columns=["variable", "state", "place_id", "probability"],
)


def make_evidence(**overrides) -> Evidence:
    defaults = dict(age="Student", budget="Low", interest="History", travel_type="Solo", weather="Sunny")
    defaults.update(overrides)
    return Evidence(**defaults)


def test_posterior_sums_to_one():
    result = score_places(make_evidence(), prior=PRIOR, cpt=CPT)
    assert abs(result["posterior"].sum() - 1.0) < 1e-9


def test_evidence_favoring_place_a_ranks_it_first():
    # Every likelihood term above is stacked in A's favor for this evidence combo.
    result = score_places(make_evidence(), prior=PRIOR, cpt=CPT)
    assert result.iloc[0]["place_id"] == "A"


def test_top_n_respects_n():
    result = top_n(make_evidence(), n=2, prior=PRIOR, cpt=CPT)
    assert len(result) == 2


def test_unknown_evidence_state_raises():
    with pytest.raises(ValueError):
        score_places(make_evidence(interest="Skiing"), prior=PRIOR, cpt=CPT)
