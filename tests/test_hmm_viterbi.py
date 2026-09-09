import pandas as pd

from recommendation_engine.hmm_viterbi import viterbi

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
