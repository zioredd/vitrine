"""Intelligence reports and command center aggregates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vitrine_types.models import Exhibition


@dataclass
class IntelligenceReport:
    exhibition_count: int
    avg_vitrine_score: float
    top_exhibitions: list[dict[str, Any]]
    alert_count: int
    catalog_stress_index: float


@dataclass
class CommandCenterSnapshot:
    active_exhibitions: int
    pending_jobs: int
    avg_intensity: float
    provenance_gaps: int
    highlights: list[str] = field(default_factory=list)


@dataclass
class DecisionReport:
    recommendation: str
    rationale: list[str]
    risk_level: str
    metrics: dict[str, float]


def build_intelligence_report(exhibitions: list[Exhibition], alerts: list[str]) -> IntelligenceReport:
    scores = [e.vitrine_score for e in exhibitions if e.vitrine_score is not None]
    avg = sum(scores) / len(scores) if scores else 0.0
    ranked = sorted(
        [{"id": e.id, "title": e.title, "score": e.vitrine_score or 0.0} for e in exhibitions],
        key=lambda x: x["score"],
        reverse=True,
    )[:5]
    stress = _catalog_stress(exhibitions)
    return IntelligenceReport(
        exhibition_count=len(exhibitions),
        avg_vitrine_score=round(avg, 2),
        top_exhibitions=ranked,
        alert_count=len(alerts),
        catalog_stress_index=round(stress, 3),
    )


def build_command_center(exhibitions: list[Exhibition], pending_jobs: int) -> CommandCenterSnapshot:
    intensities = [art.intensity for ex in exhibitions for art in ex.all_artworks()]
    avg_int = sum(intensities) / len(intensities) if intensities else 0.0
    gaps = sum(
        1
        for ex in exhibitions
        for sig in ex.signals
        if sig.provenance.confidence < 0.5 or not sig.provenance.source_url
    )
    highlights = [e.title for e in exhibitions if (e.vitrine_score or 0) >= 85][:3]
    return CommandCenterSnapshot(
        active_exhibitions=len(exhibitions),
        pending_jobs=pending_jobs,
        avg_intensity=round(avg_int, 3),
        provenance_gaps=gaps,
        highlights=highlights,
    )


def build_decision_report(exhibition: Exhibition, booking_risk: float) -> DecisionReport:
    score = exhibition.vitrine_score or 50.0
    if score >= 80 and booking_risk < 0.3:
        rec, risk = "greenlight", "low"
    elif score >= 65:
        rec, risk = "conditional", "medium"
    else:
        rec, risk = "defer", "high"
    rationale = [
        f"Vitrine score {score:.1f}",
        f"Booking risk {booking_risk:.2f}",
        f"{len(exhibition.signals)} provenance signals",
    ]
    return DecisionReport(
        recommendation=rec,
        rationale=rationale,
        risk_level=risk,
        metrics={"vitrine_score": score, "booking_risk": booking_risk},
    )


def _catalog_stress(exhibitions: list[Exhibition]) -> float:
    if not exhibitions:
        return 0.0
    thin = sum(1 for e in exhibitions if len(e.all_artworks()) < 3)
    return thin / len(exhibitions)
