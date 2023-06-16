"""Booking risk matrix across exhibitions and risk dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from vitrine_types.models import Exhibition


class RiskDimension(str, Enum):
    PROVENANCE = "provenance"
    CATALOG_DEPTH = "catalog_depth"
    CROWD_RECEPTION = "crowd_reception"
    SCHEDULING = "scheduling"
    CRAFT_QUALITY = "craft_quality"


@dataclass
class RiskCell:
    exhibition_id: str
    dimension: RiskDimension
    score: float
    weight: float
    weighted_score: float
    notes: str = ""


@dataclass
class BookingRiskMatrix:
    cells: list[RiskCell]
    row_totals: dict[str, float] = field(default_factory=dict)
    column_totals: dict[str, float] = field(default_factory=dict)
    high_risk_exhibitions: list[str] = field(default_factory=list)


_DIMENSION_WEIGHTS = {
    RiskDimension.PROVENANCE: 0.25,
    RiskDimension.CATALOG_DEPTH: 0.20,
    RiskDimension.CROWD_RECEPTION: 0.20,
    RiskDimension.SCHEDULING: 0.15,
    RiskDimension.CRAFT_QUALITY: 0.20,
}


def _provenance_risk(ex: Exhibition) -> tuple[float, str]:
    if not ex.signals:
        return 0.9, "no signals"
    low = sum(1 for s in ex.signals if s.provenance.confidence < 0.5)
    ratio = low / len(ex.signals)
    return min(1.0, ratio + (0.2 if low else 0.0)), f"{low} low-confidence signals"


def _catalog_risk(ex: Exhibition) -> tuple[float, str]:
    n = len(ex.all_artworks())
    if n < 3:
        return 0.85, "sparse catalog"
    if n < 6:
        return 0.4, "thin catalog"
    return 0.1, "adequate depth"


def _crowd_risk(ex: Exhibition) -> tuple[float, str]:
    score = ex.crowd_score
    if score is None:
        return 0.5, "missing crowd score"
    if score < 35:
        return 0.9, "poor reception"
    if score < 55:
        return 0.5, "mixed reception"
    return 0.15, "strong reception"


def _scheduling_risk(ex: Exhibition) -> tuple[float, str]:
    if ex.opened_on and ex.closed_on:
        days = (ex.closed_on - ex.opened_on).days
        if days < 14:
            return 0.7, "short run window"
        if days > 180:
            return 0.4, "extended run exposure"
    return 0.2, "standard window"


def _craft_risk(ex: Exhibition) -> tuple[float, str]:
    arts = ex.all_artworks()
    if not arts:
        return 0.8, "no craft data"
    intensities = [a.intensity for a in arts]
    span = max(intensities) - min(intensities)
    if span < 0.1:
        return 0.6, "flat intensity profile"
    if span > 0.8:
        return 0.5, "volatile pacing"
    return 0.15, "balanced craft"


_EVALUATORS = {
    RiskDimension.PROVENANCE: _provenance_risk,
    RiskDimension.CATALOG_DEPTH: _catalog_risk,
    RiskDimension.CROWD_RECEPTION: _crowd_risk,
    RiskDimension.SCHEDULING: _scheduling_risk,
    RiskDimension.CRAFT_QUALITY: _craft_risk,
}


def build_booking_risk_matrix(exhibitions: list[Exhibition]) -> BookingRiskMatrix:
    cells: list[RiskCell] = []
    for ex in exhibitions:
        for dim, weight in _DIMENSION_WEIGHTS.items():
            score, notes = _EVALUATORS[dim](ex)
            cells.append(
                RiskCell(
                    exhibition_id=ex.id,
                    dimension=dim,
                    score=round(score, 3),
                    weight=weight,
                    weighted_score=round(score * weight, 3),
                    notes=notes,
                )
            )

    row_totals: dict[str, float] = {}
    col_totals: dict[str, float] = {d.value: 0.0 for d in RiskDimension}
    for cell in cells:
        row_totals[cell.exhibition_id] = row_totals.get(cell.exhibition_id, 0.0) + cell.weighted_score
        col_totals[cell.dimension.value] += cell.weighted_score

    high_risk = [eid for eid, total in row_totals.items() if total >= 0.45]
    return BookingRiskMatrix(
        cells=cells,
        row_totals={k: round(v, 3) for k, v in row_totals.items()},
        column_totals={k: round(v / max(1, len(exhibitions)), 3) for k, v in col_totals.items()},
        high_risk_exhibitions=sorted(high_risk, key=lambda e: -row_totals[e]),
    )


def risk_heatmap(matrix: BookingRiskMatrix) -> dict[str, dict[str, float]]:
    grid: dict[str, dict[str, float]] = {}
    for cell in matrix.cells:
        grid.setdefault(cell.exhibition_id, {})[cell.dimension.value] = cell.score
    return grid
