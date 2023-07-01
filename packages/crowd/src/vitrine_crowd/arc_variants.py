"""Arc scoring variants: three-act, wave, and plateau patterns."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from vitrine_types.models import Exhibition


class ArcModel(str, Enum):
    THREE_ACT = "three_act"
    WAVE = "wave"
    PLATEAU = "plateau"


@dataclass
class ArcVariantScore:
    model: ArcModel
    score: float
    fit_quality: float
    phase_scores: dict[str, float]
    gaps: int
    recommendation: str


@dataclass
class ArcComparison:
    exhibition_id: str
    tensions: list[float]
    best_model: ArcModel
    variants: list[ArcVariantScore]
    span: float


def _tension_curve(exhibition: Exhibition) -> list[float]:
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    return [a.narrative_tension for a in arts]


def _count_gaps(tensions: list[float], threshold: float = 0.5) -> int:
    return sum(1 for i in range(len(tensions) - 1) if abs(tensions[i + 1] - tensions[i]) > threshold)


def score_three_act(tensions: list[float]) -> ArcVariantScore:
    """Classic setup → confrontation → resolution."""
    n = len(tensions)
    if n < 3:
        return ArcVariantScore(
            ArcModel.THREE_ACT, 0.0, 0.0, {}, 0, "Need at least 3 artworks for three-act structure"
        )

    third = max(1, n // 3)
    act1 = tensions[:third]
    act2 = tensions[third : 2 * third]
    act3 = tensions[2 * third :]

    a1_avg = sum(act1) / len(act1)
    a2_avg = sum(act2) / len(act2)
    a3_avg = sum(act3) / len(act3)

    rise = a2_avg > a1_avg
    resolution = a3_avg < a2_avg or abs(a3_avg - a1_avg) < 0.15
    peak_in_act2 = max(act2) >= max(act1) and max(act2) >= max(act3)

    fit_parts = [rise, resolution, peak_in_act2]
    fit_quality = sum(1.0 for p in fit_parts if p) / len(fit_parts)

    span = max(tensions) - min(tensions)
    score = fit_quality * min(1.0, span / 0.5)

    rec = "Strong three-act arc" if fit_quality >= 0.67 else "Consider raising tension in act two and resolving in act three"

    return ArcVariantScore(
        model=ArcModel.THREE_ACT,
        score=round(score, 3),
        fit_quality=round(fit_quality, 3),
        phase_scores={"act1": round(a1_avg, 3), "act2": round(a2_avg, 3), "act3": round(a3_avg, 3)},
        gaps=_count_gaps(tensions),
        recommendation=rec,
    )


def score_wave(tensions: list[float], expected_peaks: int = 2) -> ArcVariantScore:
    """Oscillating wave pattern with multiple peaks."""
    n = len(tensions)
    if n < 4:
        return ArcVariantScore(
            ArcModel.WAVE, 0.0, 0.0, {}, 0, "Need at least 4 artworks for wave pattern"
        )

    peaks = 0
    valleys = 0
    for i in range(1, n - 1):
        if tensions[i] > tensions[i - 1] and tensions[i] > tensions[i + 1]:
            peaks += 1
        if tensions[i] < tensions[i - 1] and tensions[i] < tensions[i + 1]:
            valleys += 1

    peak_match = 1.0 - min(1.0, abs(peaks - expected_peaks) / max(1, expected_peaks))
    oscillation = min(1.0, (peaks + valleys) / max(1, n // 2))
    span = max(tensions) - min(tensions)
    fit_quality = 0.5 * peak_match + 0.5 * oscillation
    score = fit_quality * min(1.0, span / 0.4)

    rec = "Wave rhythm detected" if peaks >= 2 else "Add alternating intensity peaks for wave structure"

    return ArcVariantScore(
        model=ArcModel.WAVE,
        score=round(score, 3),
        fit_quality=round(fit_quality, 3),
        phase_scores={"peaks": float(peaks), "valleys": float(valleys)},
        gaps=_count_gaps(tensions),
        recommendation=rec,
    )


def score_plateau(tensions: list[float], tolerance: float = 0.12) -> ArcVariantScore:
    """Sustained plateau with optional opening ramp."""
    n = len(tensions)
    if n < 3:
        return ArcVariantScore(
            ArcModel.PLATEAU, 0.0, 0.0, {}, 0, "Need at least 3 artworks for plateau"
        )

    mid_start = n // 4
    mid_end = (3 * n) // 4
    plateau_region = tensions[mid_start:mid_end] if mid_end > mid_start else tensions
    plateau_avg = sum(plateau_region) / len(plateau_region)
    plateau_variance = sum((t - plateau_avg) ** 2 for t in plateau_region) / len(plateau_region)

    is_flat = plateau_variance <= tolerance ** 2
    is_elevated = plateau_avg >= 0.45
    ramp = tensions[0] < plateau_avg if tensions else False

    fit_parts = [is_flat, is_elevated]
    if ramp:
        fit_parts.append(True)
    fit_quality = sum(1.0 for p in fit_parts if p) / max(1, len(fit_parts))

    score = fit_quality * plateau_avg

    rec = "Sustained plateau achieved" if is_flat else "Smooth mid-section for plateau effect"

    return ArcVariantScore(
        model=ArcModel.PLATEAU,
        score=round(score, 3),
        fit_quality=round(fit_quality, 3),
        phase_scores={"plateau_avg": round(plateau_avg, 3), "variance": round(plateau_variance, 4)},
        gaps=_count_gaps(tensions),
        recommendation=rec,
    )


def compare_arc_variants(exhibition: Exhibition) -> ArcComparison:
    """Score all arc models and pick the best fit."""
    tensions = _tension_curve(exhibition)
    variants = [
        score_three_act(tensions),
        score_wave(tensions),
        score_plateau(tensions),
    ]
    best = max(variants, key=lambda v: v.score)
    span = max(tensions) - min(tensions) if tensions else 0.0
    return ArcComparison(
        exhibition_id=exhibition.id,
        tensions=[round(t, 3) for t in tensions],
        best_model=best.model,
        variants=variants,
        span=round(span, 3),
    )


def recommend_arc_model(exhibition: Exhibition) -> tuple[ArcModel, str]:
    comparison = compare_arc_variants(exhibition)
    best = next(v for v in comparison.variants if v.model == comparison.best_model)
    return comparison.best_model, best.recommendation


def arc_model_score(
    exhibition: Exhibition,
    model: ArcModel | str,
) -> ArcVariantScore:
    tensions = _tension_curve(exhibition)
    model_enum = ArcModel(model) if isinstance(model, str) else model
    if model_enum == ArcModel.THREE_ACT:
        return score_three_act(tensions)
    if model_enum == ArcModel.WAVE:
        return score_wave(tensions)
    return score_plateau(tensions)
