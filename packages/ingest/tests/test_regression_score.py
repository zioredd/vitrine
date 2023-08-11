"""Regression: normalize_score must clamp outliers."""

from vitrine_ingest.pipeline import normalize_score


def test_normalize_score_clamps_high_outliers():
    assert normalize_score(150) == 100.0
