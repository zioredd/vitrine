"""Multi-scenario what-if engine for exhibition scoring projections."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from vitrine_types.models import Exhibition


class ScenarioKind(str, Enum):
    INTENSITY_BOOST = "intensity_boost"
    SIGNAL_INJECTION = "signal_injection"
    CROWD_SHIFT = "crowd_shift"
    DWELL_OPTIMIZATION = "dwell_optimization"
    PROVENANCE_UPGRADE = "provenance_upgrade"


@dataclass
class ScenarioInput:
    kind: ScenarioKind
    magnitude: float = 0.1
    label: str = ""


@dataclass
class ScenarioOutcome:
    kind: ScenarioKind
    baseline_score: float
    projected_score: float
    delta: float
    confidence: float
    assumptions: list[str] = field(default_factory=list)


@dataclass
class ScenarioPlan:
    exhibition_id: str
    baseline_score: float
    outcomes: list[ScenarioOutcome]
    best_scenario: ScenarioOutcome | None
    composite_projection: float


def _baseline(ex: Exhibition) -> float:
    return ex.vitrine_score or ex.crowd_score or 50.0


def _apply_intensity_boost(ex: Exhibition, magnitude: float) -> float:
    arts = ex.all_artworks()
    if not arts:
        return _baseline(ex)
    avg_int = sum(a.intensity for a in arts) / len(arts)
    craft = min(100.0, (avg_int + magnitude) * 100)
    base = _baseline(ex)
    return 0.55 * base + 0.45 * craft


def _apply_signal_injection(ex: Exhibition, magnitude: float) -> float:
    base = _baseline(ex)
    if not ex.signals:
        return base + magnitude * 20
    avg_sig = sum(s.score for s in ex.signals) / len(ex.signals)
    boost = (100.0 - avg_sig) * magnitude * 0.5
    return min(100.0, base + boost)


def _apply_crowd_shift(ex: Exhibition, magnitude: float) -> float:
    crowd = ex.crowd_score or 50.0
    shifted = min(100.0, crowd + magnitude * 100)
    base = _baseline(ex)
    return 0.4 * base + 0.6 * shifted


def _apply_dwell_optimization(ex: Exhibition, magnitude: float) -> float:
    arts = ex.all_artworks()
    if not arts:
        return _baseline(ex)
    avg_dwell = sum(a.dwell_sec for a in arts) / len(arts)
    optimal = 180.0
    improvement = max(0.0, 1.0 - abs(avg_dwell - optimal) / optimal)
    base = _baseline(ex)
    return min(100.0, base + improvement * magnitude * 30)


def _apply_provenance_upgrade(ex: Exhibition, magnitude: float) -> float:
    if not ex.signals:
        return _baseline(ex)
    avg_conf = sum(s.provenance.confidence for s in ex.signals) / len(ex.signals)
    upgraded = min(1.0, avg_conf + magnitude)
    base = _baseline(ex)
    return min(100.0, base + (upgraded - avg_conf) * 25)


_APPLIERS = {
    ScenarioKind.INTENSITY_BOOST: _apply_intensity_boost,
    ScenarioKind.SIGNAL_INJECTION: _apply_signal_injection,
    ScenarioKind.CROWD_SHIFT: _apply_crowd_shift,
    ScenarioKind.DWELL_OPTIMIZATION: _apply_dwell_optimization,
    ScenarioKind.PROVENANCE_UPGRADE: _apply_provenance_upgrade,
}


def run_scenario(ex: Exhibition, scenario: ScenarioInput) -> ScenarioOutcome:
    base = _baseline(ex)
    applier = _APPLIERS[scenario.kind]
    projected = applier(ex, scenario.magnitude)
    delta = projected - base
    confidence = min(1.0, 0.5 + scenario.magnitude)
    return ScenarioOutcome(
        kind=scenario.kind,
        baseline_score=round(base, 2),
        projected_score=round(projected, 2),
        delta=round(delta, 2),
        confidence=round(confidence, 3),
        assumptions=[f"{scenario.kind.value} magnitude={scenario.magnitude}"],
    )


def run_scenario_plan(
    ex: Exhibition,
    scenarios: list[ScenarioInput] | None = None,
) -> ScenarioPlan:
    scenarios = scenarios or [
        ScenarioInput(ScenarioKind.INTENSITY_BOOST, 0.1),
        ScenarioInput(ScenarioKind.SIGNAL_INJECTION, 0.15),
        ScenarioInput(ScenarioKind.CROWD_SHIFT, 0.08),
        ScenarioInput(ScenarioKind.DWELL_OPTIMIZATION, 0.12),
        ScenarioInput(ScenarioKind.PROVENANCE_UPGRADE, 0.1),
    ]
    outcomes = [run_scenario(ex, s) for s in scenarios]
    best = max(outcomes, key=lambda o: o.delta) if outcomes else None
    composite = sum(o.projected_score for o in outcomes) / len(outcomes) if outcomes else _baseline(ex)
    return ScenarioPlan(
        exhibition_id=ex.id,
        baseline_score=round(_baseline(ex), 2),
        outcomes=outcomes,
        best_scenario=best,
        composite_projection=round(composite, 2),
    )


def compare_scenarios_across_catalog(
    exhibitions: list[Exhibition],
    kind: ScenarioKind,
    magnitude: float = 0.1,
) -> list[tuple[str, float]]:
    """Return exhibition ids sorted by scenario delta descending."""
    results: list[tuple[str, float]] = []
    scenario = ScenarioInput(kind=kind, magnitude=magnitude)
    for ex in exhibitions:
        outcome = run_scenario(ex, scenario)
        results.append((ex.id, outcome.delta))
    return sorted(results, key=lambda x: -x[1])
