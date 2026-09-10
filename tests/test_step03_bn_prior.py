from math import log

from data_generation.step03_bn_prior import FLOOR_SCORE, _popularity_score


def test_score_with_rating_and_review_count():
    score, note = _popularity_score(4.5, 999)
    assert score == 4.5 * log(1000)
    assert "ln(review_count" in note


def test_score_with_rating_only():
    score, note = _popularity_score(4.0, None)
    assert score == 4.0
    assert "rating only" in note


def test_score_with_no_evidence_uses_floor():
    score, note = _popularity_score(None, None)
    assert score == FLOOR_SCORE
    assert "floor score" in note


def test_more_reviews_scores_higher_at_equal_rating():
    low, _ = _popularity_score(4.0, 10)
    high, _ = _popularity_score(4.0, 10_000)
    assert high > low


def test_floor_is_never_zero():
    assert FLOOR_SCORE > 0
