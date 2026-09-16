import pandas as pd
import pytest

from recommendation_engine.hmm_viterbi import (
    TIME_SLOTS,
    _restrict_emission,
    _restrict_initial,
    _restrict_transition,
    decode_sequence,
    viterbi,
)

STATES = ["X", "Y"]


def test_viterbi_follows_a_dominant_emission_path():
    # Observation 1 strongly favors X, observation 2 strongly favors Y, observation 3
    # strongly favors X again; a near-uniform transition matrix shouldn't override that.
    pi = pd.Series([0.5, 0.5], index=STATES)
    A = pd.DataFrame([[0.5, 0.5], [0.5, 0.5]], index=STATES, columns=STATES)
    B = pd.DataFrame(
        {"obs1": [0.95, 0.05], "obs2": [0.05, 0.95], "obs3": [0.9, 0.1]},
        index=STATES,
    )

    path = viterbi(pi, A, B, ["obs1", "obs2", "obs3"])
    assert path == ["X", "Y", "X"]


def test_viterbi_returns_one_state_per_observation():
    pi = pd.Series([0.3, 0.7], index=STATES)
    A = pd.DataFrame([[0.8, 0.2], [0.1, 0.9]], index=STATES, columns=STATES)
    B = pd.DataFrame({"a": [0.6, 0.4], "b": [0.4, 0.6]}, index=STATES)

    path = viterbi(pi, A, B, ["a", "b", "a", "b"])
    assert len(path) == 4
    assert all(s in STATES for s in path)


# ---------------------------------------------------------------------------
# Long-format table loaders (04/05/06 -> pi / A / B). None of the fixtures below
# use the old wide from_place_id/P01..P20 columns or the old 'pi' column name --
# proves the restrict_* functions have no remaining dependency on that format.
# ---------------------------------------------------------------------------

PLACE_IDS = ["P01", "P02", "P03"]


def _initial_df():
    return pd.DataFrame(
        {"place_id": ["P01", "P02", "P03", "P04"], "initial_probability": [0.4, 0.35, 0.15, 0.10]}
    )


def _transition_df():
    # Long format: one row per ordered (from_id, to_id) pair. Self-transitions are
    # intentionally absent, matching 05_HMM_Transition's real policy.
    rows = []
    for from_id in ["P01", "P02", "P03", "P04"]:
        for to_id in ["P01", "P02", "P03", "P04"]:
            if from_id == to_id:
                continue
            rows.append({"from_id": from_id, "to_id": to_id, "transition_probability": 1.0 / 3})
    return pd.DataFrame(rows)


def _emission_df():
    rows = []
    for pid in ["P01", "P02", "P03", "P04"]:
        for slot in TIME_SLOTS:
            rows.append({"place_id": pid, "slot": slot, "probability": 1.0 / len(TIME_SLOTS)})
    return pd.DataFrame(rows)


def test_restrict_initial_reads_initial_probability_column():
    pi = _restrict_initial(_initial_df(), PLACE_IDS)
    assert list(pi.index) == PLACE_IDS
    assert pi.sum() == pytest.approx(1.0)


def test_restrict_initial_missing_place_raises_clear_error():
    with pytest.raises(ValueError, match="P99"):
        _restrict_initial(_initial_df(), ["P01", "P99"])


def test_restrict_transition_builds_from_id_to_id_lookup():
    A = _restrict_transition(_transition_df(), PLACE_IDS)
    assert list(A.index) == PLACE_IDS
    assert list(A.columns) == PLACE_IDS
    # Self-transitions are filled in as an explicit 0, not raised as missing data.
    assert A.loc["P01", "P01"] == 0.0
    row_sums = A.sum(axis=1)
    assert (abs(row_sums - 1.0) < 1e-9).all()


def test_restrict_transition_missing_pair_raises_clear_error():
    df = _transition_df()
    df = df[~((df["from_id"] == "P01") & (df["to_id"] == "P02"))]  # drop one required pair
    with pytest.raises(ValueError, match="P01.*P02|P02.*P01"):
        _restrict_transition(df, PLACE_IDS)


def test_restrict_transition_rejects_a_zero_total_row_instead_of_inventing_uniform():
    # Every real transition_probability is strictly positive (1/(travel_time+eps) is
    # never exactly 0), so a restricted row summing to 0 is a genuine data anomaly --
    # must raise rather than silently substitute a uniform distribution.
    df = _transition_df().copy()
    df.loc[(df["from_id"] == "P01") & (df["to_id"].isin(["P02", "P03"])), "transition_probability"] = 0.0
    with pytest.raises(ValueError, match="P01"):
        _restrict_transition(df, PLACE_IDS)


def test_restrict_emission_reads_place_id_and_slot():
    B = _restrict_emission(_emission_df(), PLACE_IDS, TIME_SLOTS)
    assert list(B.index) == PLACE_IDS
    assert list(B.columns) == TIME_SLOTS
    assert (abs(B.sum(axis=1) - 1.0) < 1e-9).all()


def test_restrict_emission_missing_place_raises_clear_error():
    with pytest.raises(ValueError, match="P99"):
        _restrict_emission(_emission_df(), ["P01", "P99"], TIME_SLOTS)


def test_restrict_emission_missing_slot_raises_clear_error():
    with pytest.raises(ValueError, match="Night"):
        _restrict_emission(_emission_df(), PLACE_IDS, ["Morning", "Night"])


def test_top_n_filtering_excludes_unselected_places():
    pi = _restrict_initial(_initial_df(), PLACE_IDS)
    A = _restrict_transition(_transition_df(), PLACE_IDS)
    B = _restrict_emission(_emission_df(), PLACE_IDS, TIME_SLOTS)
    assert "P04" not in pi.index
    assert "P04" not in A.index and "P04" not in A.columns
    assert "P04" not in B.index


def test_decode_sequence_works_on_real_project_data():
    # Integration test against the actual finalized workbook tables (no network
    # needed, just reads data/BayesTrip_Data.xlsx) -- proves the long-format loaders
    # work with the real 04/05/06 schemas, not just synthetic fixtures.
    from data_generation.common.places import PLACES

    place_ids = [p["place_id"] for p in PLACES[:5]]
    sequence = decode_sequence(place_ids)
    assert len(sequence) == len(TIME_SLOTS)
    assert all(pid in place_ids for pid in sequence)
