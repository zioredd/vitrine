"""Scoring engine: freshness decay, composite Vitrine Score, normalization."""

from __future__ import annotations

import math
from datetime import date


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def rank_normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    mn, mx = min(values), max(values)
    if math.isclose(mn, mx):
        return [50.0 for _ in values]
    span = mx - mn
    return [clamp(50.0 + 50.0 * ((v - mn) / span) * 2.0 - 50.0) for v in values]


def freshness_decay(base_score: float, reference: date, today: date | None = None) -> float:
    """Exponential half-life decay over 180 days."""
    today = today or date.today()
    age_days = max(0, (today - reference).days)
    half_life = 180.0
    factor = math.pow(0.5, age_days / half_life)
    return clamp(base_score * factor)


def composite_vitrine_score(
    signal_scores: list[float],
    craft_score: float,
    crowd_score: float,
    weights: tuple[float, float, float] = (0.45, 0.30, 0.25),
) -> float:
    w_sig, w_craft, w_crowd = weights
    signal_avg = sum(signal_scores) / len(signal_scores) if signal_scores else 50.0
    raw = w_sig * signal_avg + w_craft * craft_score + w_crowd * crowd_score
    return clamp(raw)


def weighted_signal_blend(scores: list[float], weights: list[float]) -> float:
    if not scores:
        return 50.0
    if len(weights) != len(scores):
        weights = [1.0] * len(scores)
    total_w = sum(weights) or 1.0
    return sum(s * w for s, w in zip(scores, weights)) / total_w
