from data_generation.step07_hmm_emission import CLOSED_FLOOR, FULL_SCORE, PARTIAL_SCORE, SLOTS, build


def test_row_count():
    df = build()
    assert len(df) == 20 * len(SLOTS)


def test_every_place_sums_to_one():
    df = build()
    sums = df.groupby("place_id")["probability"].sum()
    assert (sums - 1.0).abs().max() < 1e-9


def test_raw_scores_use_only_the_three_defined_levels():
    df = build()
    assert set(df["raw_score"].unique()) <= {FULL_SCORE, PARTIAL_SCORE, CLOSED_FLOOR}


def test_closed_floor_is_never_exactly_zero():
    df = build()
    assert (df["probability"] > 0).all()
