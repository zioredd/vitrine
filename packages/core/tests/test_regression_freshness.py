"""Regression: freshness decay half-life."""

from datetime import date, timedelta

from vitrine_core.scoring import freshness_decay


def test_freshness_decay_180_day_half_life():
    base = 100.0
    ref = date(2024, 1, 1)
    mid = freshness_decay(base, ref, ref + timedelta(days=180))
    assert 49 <= mid <= 51
