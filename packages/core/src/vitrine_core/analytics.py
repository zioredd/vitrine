"""Audience cohorts, provenance audit, catalog stress, simulator, alerts."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from vitrine_core.alerts import AlertReport, EscalatedAlert, run_alert_engine
from vitrine_core.booking_matrix import BookingRiskMatrix, build_booking_risk_matrix
from vitrine_core.cohorts import ClusteringResult, cluster_audience_cohorts
from vitrine_core.provenance_trails import AuditTrailReport, audit_trails
from vitrine_core.royalty import RoyaltyCalculation, calculate_royalty_tier, royalty_portfolio_summary
from vitrine_core.scenarios import ScenarioPlan, run_scenario_plan
from vitrine_core.stress_simulator import CatalogStressSimulation, simulate_catalog_stress
from vitrine_types.models import Exhibition


@dataclass
class CohortSummary:
    name: str
    size: int
    avg_score: float


@dataclass
class ProvenanceAudit:
    total_signals: int
    low_confidence: int
    missing_url: int
    by_source: dict[str, int]


@dataclass
class WhatIfResult:
    baseline_score: float
    projected_score: float
    delta: float
    assumptions: list[str]


@dataclass
class Alert:
    code: str
    message: str
    severity: str


def audience_cohorts(exhibitions: list[Exhibition]) -> list[CohortSummary]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for ex in exhibitions:
        genre = ex.genre or "general"
        score = ex.vitrine_score or ex.crowd_score or 50.0
        buckets[genre].append(score)
    return [
        CohortSummary(name=k, size=len(v), avg_score=round(sum(v) / len(v), 2))
        for k, v in sorted(buckets.items())
    ]


def provenance_audit(exhibitions: list[Exhibition]) -> ProvenanceAudit:
    total = low = missing = 0
    sources: Counter[str] = Counter()
    for ex in exhibitions:
        for sig in ex.signals:
            total += 1
            sources[sig.provenance.source_name] += 1
            if sig.provenance.confidence < 0.5:
                low += 1
            if not sig.provenance.source_url:
                missing += 1
    return ProvenanceAudit(
        total_signals=total,
        low_confidence=low,
        missing_url=missing,
        by_source=dict(sources),
    )


def catalog_stress_index(exhibitions: list[Exhibition]) -> float:
    if not exhibitions:
        return 0.0
    sim = simulate_catalog_stress(exhibitions)
    return sim.projected_index


def what_if_simulator(exhibition: Exhibition, intensity_boost: float = 0.1) -> WhatIfResult:
    plan = run_scenario_plan(exhibition)
    best = plan.best_scenario
    if best is None:
        base = exhibition.vitrine_score or 50.0
        return WhatIfResult(base, base, 0.0, ["no scenarios"])
    return WhatIfResult(
        baseline_score=best.baseline_score,
        projected_score=best.projected_score,
        delta=best.delta,
        assumptions=best.assumptions,
    )


def alert_engine(exhibitions: list[Exhibition]) -> list[Alert]:
    report = run_alert_engine(exhibitions)
    return [
        Alert(
            code=a.code,
            message=a.message,
            severity=a.severity.name.lower(),
        )
        for a in report.alerts
        if a.escalation_level == 0
    ]


__all__ = [
    "Alert",
    "AlertReport",
    "AuditTrailReport",
    "BookingRiskMatrix",
    "CatalogStressSimulation",
    "ClusteringResult",
    "CohortSummary",
    "EscalatedAlert",
    "ProvenanceAudit",
    "RoyaltyCalculation",
    "ScenarioPlan",
    "WhatIfResult",
    "alert_engine",
    "audience_cohorts",
    "audit_trails",
    "build_booking_risk_matrix",
    "calculate_royalty_tier",
    "catalog_stress_index",
    "cluster_audience_cohorts",
    "provenance_audit",
    "royalty_portfolio_summary",
    "run_alert_engine",
    "run_scenario_plan",
    "simulate_catalog_stress",
    "what_if_simulator",
]
