"""HMM over the Top-5 recommended places, decoded with Viterbi to produce a visiting
sequence.

Hidden state = which place is being visited; observations = the fixed time-of-day
sequence [Morning, Afternoon, Evening]. The full 20-place pi / transition / emission
tables (04/05/06) are restricted to the Top-5 place_ids and re-normalized, since a
same-day itinerary only ever moves between the recommended places.
"""

import numpy as np
import pandas as pd

from data_generation.common.workbook import read_sheet

TIME_SLOTS = ["Morning", "Afternoon", "Evening"]


def _restrict_initial(initial: pd.DataFrame, place_ids: list[str]) -> pd.Series:
    pi = initial.set_index("place_id")["pi"].reindex(place_ids).astype(float)
    return pi / pi.sum()


def _restrict_transition(transition: pd.DataFrame, place_ids: list[str]) -> pd.DataFrame:
    sub = transition.set_index("from_place_id").loc[place_ids, place_ids].astype(float)
    row_sums = sub.sum(axis=1)
    # A place with zero probability to every other place in this Top-5 set (all mass
    # was on places outside the set) gets a uniform fallback row so Viterbi still has
    # a valid transition distribution to work with.
    zero_rows = row_sums == 0
    if zero_rows.any():
        sub.loc[zero_rows, :] = 1.0 / len(place_ids)
        row_sums = sub.sum(axis=1)
    return sub.div(row_sums, axis=0)


def _restrict_emission(emission: pd.DataFrame, place_ids: list[str]) -> pd.DataFrame:
    sub = emission[emission["place_id"].isin(place_ids)]
    pivot = sub.pivot(index="place_id", columns="slot", values="probability").loc[place_ids, TIME_SLOTS].astype(float)
    return pivot


def viterbi(pi: pd.Series, A: pd.DataFrame, B: pd.DataFrame, observations: list[str]) -> list[str]:
    """Standard log-space Viterbi. pi: Series indexed by state. A: DataFrame [state, state].
    B: DataFrame [state, observation]. Returns the most likely state sequence."""
    states = list(pi.index)
    n_states = len(states)
    n_obs = len(observations)

    log_pi = np.log(pi.values + 1e-300)
    log_A = np.log(A.values + 1e-300)
    log_B = np.log(B[observations].values + 1e-300)

    delta = np.zeros((n_obs, n_states))
    psi = np.zeros((n_obs, n_states), dtype=int)

    delta[0] = log_pi + log_B[:, 0]
    for t in range(1, n_obs):
        for j in range(n_states):
            candidates = delta[t - 1] + log_A[:, j]
            psi[t, j] = int(np.argmax(candidates))
            delta[t, j] = candidates[psi[t, j]] + log_B[j, t]

    path = [int(np.argmax(delta[-1]))]
    for t in range(n_obs - 1, 0, -1):
        path.append(psi[t, path[-1]])
    path.reverse()

    return [states[i] for i in path]


def decode_sequence(place_ids: list[str], observations: list[str] | None = None) -> list[str]:
    observations = observations or TIME_SLOTS
    initial = read_sheet("04_HMM_Initial")
    transition = read_sheet("05_HMM_Transition")
    emission = read_sheet("06_HMM_Emission")

    pi = _restrict_initial(initial, place_ids)
    A = _restrict_transition(transition, place_ids)
    B = _restrict_emission(emission, place_ids)

    return viterbi(pi, A, B, observations)
