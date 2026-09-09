from data_generation.step04_bn_cpt import VARIABLE_STATES, build


def test_row_count():
    df = build()
    assert len(df) == 20 * sum(len(states) for states in VARIABLE_STATES.values())


def test_every_group_sums_to_one():
    df = build()
    sums = df.groupby(["place_id", "variable"])["probability"].sum()
    assert (sums - 1.0).abs().max() < 1e-9


def test_every_place_has_every_variable_state():
    df = build()
    for place_id, place_df in df.groupby("place_id"):
        for variable, states in VARIABLE_STATES.items():
            got = set(place_df.loc[place_df["variable"] == variable, "state"])
            assert got == set(states), f"{place_id}/{variable}: expected {states}, got {got}"


def test_probabilities_are_nonnegative():
    df = build()
    assert (df["probability"] >= 0).all()
