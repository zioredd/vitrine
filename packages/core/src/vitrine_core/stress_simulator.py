"""Catalog stress simulation and load modeling."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from vitrine_types.models import Exhibition


@dataclass
class StressFactor:
    name: str
    weight: float
    value: float
    contribution: float


@dataclass
class ExhibitionStressProfile:
    exhibition_id: str
    stress_index: float
    factors: list[StressFactor]
    risk_band: str


@dataclass
class CatalogStressSimulation:
    baseline_index: float
    projected_index: float
    profiles: list[ExhibitionStressProfile]
    bottleneck_exhibitions: list[str]
    recommendations: list[str]


def _compute_factors(ex: Exhibition) -> list[StressFactor]:
    factors: list[StressFactor] = []
    n_art = len(ex.all_artworks())
    n_sig = len(ex.signals)
    n_nodes = len(ex.graph_nodes)

    sparse = 1.0 if n_art < 4 else max(0.0, (4 - n_art) / 4)
    factors.append(StressFactor("sparse_catalog", 0.35, sparse, round(sparse * 0.35, 3)))

    signal_gap = 1.0 if n_sig < 2 else max(0.0, (2 - n_sig) / 2)
    factors.append(StressFactor("signal_gap", 0.25, signal_gap, round(signal_gap * 0.25, 3)))

    graph_gap = 1.0 if n_nodes == 0 else 0.0
    factors.append(StressFactor("graph_gap", 0.20, graph_gap, round(graph_gap * 0.20, 3)))

    score = ex.vitrine_score or 50.0
    score_stress = max(0.0, (40.0 - score) / 40.0) if score < 40 else 0.0
    factors.append(StressFactor("low_score", 0.20, score_stress, round(score_stress * 0.20, 3)))

    return factors


def profile_exhibition_stress(ex: Exhibition) -> ExhibitionStressProfile:
    factors = _compute_factors(ex)
    index = min(1.0, sum(f.contribution for f in factors))
    if index >= 0.7:
        band = "critical"
    elif index >= 0.4:
        band = "elevated"
    elif index >= 0.2:
        band = "moderate"
    else:
        band = "healthy"
    return ExhibitionStressProfile(
        exhibition_id=ex.id,
        stress_index=round(index, 3),
        factors=factors,
        risk_band=band,
    )


def simulate_catalog_stress(
    exhibitions: list[Exhibition],
    removal_pct: float = 0.0,
    signal_dropout: float = 0.0,
    seed: int = 0,
) -> CatalogStressSimulation:
    """Simulate catalog stress under artifact loss or signal dropout."""
    rng = random.Random(seed)
    baseline_profiles = [profile_exhibition_stress(ex) for ex in exhibitions]
    baseline = sum(p.stress_index for p in baseline_profiles) / max(1, len(baseline_profiles))

    simulated: list[Exhibition] = []
    for ex in exhibitions:
        if rng.random() < removal_pct:
            continue
        if signal_dropout > 0 and ex.signals:
            keep = max(1, int(len(ex.signals) * (1.0 - signal_dropout)))
            new_ex = ex.model_copy(update={"signals": ex.signals[:keep]})
            simulated.append(new_ex)
        else:
            simulated.append(ex)

    projected_profiles = [profile_exhibition_stress(ex) for ex in simulated]
    projected = sum(p.stress_index for p in projected_profiles) / max(1, len(projected_profiles))

    bottlenecks = [p.exhibition_id for p in projected_profiles if p.risk_band == "critical"]
    recs: list[str] = []
    if projected > baseline + 0.1:
        recs.append("Catalog stress rising — prioritize provenance enrichment")
    if bottlenecks:
        recs.append(f"{len(bottlenecks)} exhibitions in critical stress band")
    if signal_dropout > 0.2:
        recs.append("Signal dropout scenario exceeds tolerance — audit ingest pipeline")

    return CatalogStressSimulation(
        baseline_index=round(baseline, 3),
        projected_index=round(projected, 3),
        profiles=projected_profiles,
        bottleneck_exhibitions=bottlenecks,
        recommendations=recs or ["Catalog within stress tolerance"],
    )


def stress_heatmap(
    exhibitions: list[Exhibition],
    residency_bins: bool = True,
) -> dict[str, float]:
    """Aggregate stress by residency or genre bucket."""
    buckets: dict[str, list[float]] = {}
    for ex in exhibitions:
        key = ex.residency if residency_bins and ex.residency else (ex.genre or "general")
        profile = profile_exhibition_stress(ex)
        buckets.setdefault(key, []).append(profile.stress_index)
    return {k: round(sum(v) / len(v), 3) for k, v in sorted(buckets.items())}
