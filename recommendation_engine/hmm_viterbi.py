
import numpy as np
import pandas as pd

from data_generation.common.workbook import read_sheet

TIME_SLOTS = ["Morning", "Afternoon", "Evening"]


def _position_time_slots(n: int) -> list[str]:
    """Maps n chronological itinerary positions onto the existing 3 emission time
    slots, distributing them as evenly as possible in slot order (earlier slots get
    any remainder) -- no new emission data is invented, every position just reuses
    one of the existing Morning/Afternoon/Evening probabilities. For the project's
    real case (n=5): [Morning, Morning, Afternoon, Afternoon, Evening]."""
    base, extra = divmod(n, len(TIME_SLOTS))
    slots = []
    for i, slot in enumerate(TIME_SLOTS):
        count = base + (1 if i < extra else 0)
        slots.extend([slot] * count)
    return slots


def _restrict_initial(initial: pd.DataFrame, place_ids: list[str]) -> pd.Series:
    """04_HMM_Initial: one row per place_id, with an `initial_probability` column."""
    lookup = initial.set_index("place_id")["initial_probability"]

    missing = [pid for pid in place_ids if pid not in lookup.index]
    if missing:
        raise ValueError(f"04_HMM_Initial has no row for place_id(s): {missing}")

    pi = lookup.reindex(place_ids).astype(float)
    null_ids = pi[pi.isna()].index.tolist()
    if null_ids:
        raise ValueError(f"04_HMM_Initial has a null initial_probability for place_id(s): {null_ids}")

    total = pi.sum()
    if total <= 0:
        raise ValueError(f"Sum of restricted initial probabilities for {place_ids} is not positive; cannot normalize")
    return pi / total


def _restrict_transition(transition: pd.DataFrame, place_ids: list[str]) -> pd.DataFrame:
    """05_HMM_Transition: one row per ordered (from_id, to_id) pair, with a
    `transition_probability` column. Self-transitions (from_id == to_id) are not
    present in the table at all -- that absence IS the model's explicit A[i][i] = 0
    policy (see DESIGN.md), not missing data, so it's filled in as 0.0 here rather
    than raised as an error. Any OTHER missing (from_id, to_id) pair among the
    requested place_ids is treated as a real data error."""
    lookup = transition.set_index(["from_id", "to_id"])["transition_probability"]

    matrix = pd.DataFrame(0.0, index=place_ids, columns=place_ids)
    for from_id in place_ids:
        for to_id in place_ids:
            if from_id == to_id:
                continue  # explicit A[i][i] = 0, per this project's self-transition policy
            key = (from_id, to_id)
            if key not in lookup.index:
                raise ValueError(f"05_HMM_Transition has no row for from_id={from_id!r}, to_id={to_id!r}")
            value = lookup.loc[key]
            if pd.isna(value):
                raise ValueError(f"05_HMM_Transition has a null transition_probability for from_id={from_id!r}, to_id={to_id!r}")
            matrix.loc[from_id, to_id] = float(value)

    row_sums = matrix.sum(axis=1)
    # Every transition_probability in the real 05_HMM_Transition data is strictly
    # positive (raw_transition_score = 1/(travel_time_min + eps) can never be exactly
    # 0), so a restricted row summing to 0 would mean a genuine data anomaly, not an
    # expected edge case -- raise rather than silently substitute a uniform guess.
    zero_rows = row_sums[row_sums == 0].index.tolist()
    if zero_rows:
        raise ValueError(
            f"05_HMM_Transition: from_id(s) {zero_rows} have zero total transition probability "
            f"among place_ids {place_ids} -- cannot normalize without inventing a distribution"
        )
    return matrix.div(row_sums, axis=0)


def _restrict_emission(emission: pd.DataFrame, place_ids: list[str], observations: list[str]) -> pd.DataFrame:
    """06_HMM_Emission: one row per (place_id, slot), with a `probability` column."""
    sub = emission[emission["place_id"].isin(place_ids)]

    missing_places = [pid for pid in place_ids if pid not in set(sub["place_id"])]
    if missing_places:
        raise ValueError(f"06_HMM_Emission has no rows for place_id(s): {missing_places}")

    pivot = sub.pivot(index="place_id", columns="slot", values="probability")

    missing_slots = [o for o in observations if o not in pivot.columns]
    if missing_slots:
        raise ValueError(f"06_HMM_Emission is missing observation slot(s): {missing_slots}")

    pivot = pivot.loc[place_ids, observations].astype(float)
    if pivot.isna().any().any():
        bad_cells = [(pid, obs) for pid in place_ids for obs in observations if pd.isna(pivot.loc[pid, obs])]
        raise ValueError(f"06_HMM_Emission has a null probability for (place_id, slot): {bad_cells}")

    return pivot


def viterbi(pi: pd.Series, A: pd.DataFrame, B: pd.DataFrame, observations: list[str]) -> list[str]:
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


def viterbi_unique_sequence(pi: pd.Series, A: pd.DataFrame, B: pd.DataFrame, position_slots: list[str]) -> list[str]:
   
    states = list(pi.index)
    n = len(states)
    if len(position_slots) != n:
        raise ValueError(f"position_slots length ({len(position_slots)}) must equal the number of states ({n})")
    if B.shape[1] != n:
        raise ValueError(f"B has {B.shape[1]} columns but expected {n} (one per position_slots entry)")

    log_pi = np.log(pi.values + 1e-300)
    log_A = np.log(A.values + 1e-300)
    log_B = np.log(B.values + 1e-300)  # positional: column t is the t-th position_slots entry

    full_mask = (1 << n) - 1
    NEG_INF = float("-inf")

    delta = [[NEG_INF] * n for _ in range(1 << n)]
    psi = [[-1] * n for _ in range(1 << n)]

    for j in range(n):
        mask = 1 << j
        delta[mask][j] = log_pi[j] + log_B[j, 0]

    for mask in range(1, 1 << n):
        popcount = bin(mask).count("1")
        if popcount < 2:
            continue
        position_index = popcount - 1
        for j in range(n):
            if not (mask & (1 << j)):
                continue
            prev_mask = mask & ~(1 << j)
            best_val, best_i = NEG_INF, -1
            for i in range(n):
                if i == j or not (prev_mask & (1 << i)) or delta[prev_mask][i] == NEG_INF:
                    continue
                val = delta[prev_mask][i] + log_A[i, j]
                if val > best_val:
                    best_val, best_i = val, i
            if best_i == -1:
                continue
            delta[mask][j] = best_val + log_B[j, position_index]
            psi[mask][j] = best_i

    best_final, best_j = NEG_INF, -1
    for j in range(n):
        if delta[full_mask][j] > best_final:
            best_final, best_j = delta[full_mask][j], j

    if best_j == -1:
        raise ValueError(
            "No valid full-visitation ordering found across the given states -- check pi/A/B "
            "for zero-probability entries that block every possible ordering"
        )

    sequence_idx = []
    mask, j = full_mask, best_j
    while True:
        sequence_idx.append(j)
        prev_j = psi[mask][j]
        mask &= ~(1 << j)
        if prev_j == -1:
            break
        j = prev_j
    sequence_idx.reverse()

    return [states[i] for i in sequence_idx]


def decode_sequence(place_ids: list[str], observations: list[str] | None = None) -> list[str]:
    """Returns the highest-probability ORDERED PERMUTATION of place_ids -- each place
    visited exactly once -- via viterbi_unique_sequence(). If observations isn't
    given, itinerary positions are auto-mapped onto the existing emission time slots
    via _position_time_slots(len(place_ids))."""
    position_slots = observations or _position_time_slots(len(place_ids))
    if len(position_slots) != len(place_ids):
        raise ValueError(f"observations length ({len(position_slots)}) must equal place_ids length ({len(place_ids)})")

    initial = read_sheet("04_HMM_Initial")
    transition = read_sheet("05_HMM_Transition")
    emission = read_sheet("06_HMM_Emission")

    pi = _restrict_initial(initial, place_ids)
    A = _restrict_transition(transition, place_ids)
    B = _restrict_emission(emission, place_ids, position_slots)

    return viterbi_unique_sequence(pi, A, B, position_slots)
