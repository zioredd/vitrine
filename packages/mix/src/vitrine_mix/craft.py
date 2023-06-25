"""Craft analytics: pacing curve, energy map, transition density."""

from __future__ import annotations

import math
from dataclasses import dataclass

from vitrine_types.models import Artwork, Exhibition


@dataclass
class PacingPoint:
    position: int
    intensity: float
    dwell_sec: float
    cumulative_dwell: float


@dataclass
class EnergyZone:
    start: int
    end: int
    avg_intensity: float
    label: str


@dataclass
class TransitionMetrics:
    count: int
    avg_delta: float
    max_delta: float
    density: float


@dataclass
class CraftReport:
    pacing_score: float
    wall_text_ratio: float
    transition_density: float
    energy_zones: list[EnergyZone]


def pacing_curve(artworks: list[Artwork]) -> list[PacingPoint]:
    """Build cumulative pacing curve from ordered artwork samples."""
    ordered = sorted(artworks, key=lambda a: a.position)
    cumulative = 0.0
    points: list[PacingPoint] = []
    for art in ordered:
        cumulative += art.dwell_sec
        points.append(
            PacingPoint(
                position=art.position,
                intensity=art.intensity,
                dwell_sec=art.dwell_sec,
                cumulative_dwell=cumulative,
            )
        )
    return points


def energy_map(artworks: list[Artwork], zone_size: int = 3) -> list[EnergyZone]:
    """Segment artworks into zones by average intensity."""
    ordered = sorted(artworks, key=lambda a: a.position)
    zones: list[EnergyZone] = []
    for i in range(0, len(ordered), zone_size):
        chunk = ordered[i : i + zone_size]
        if not chunk:
            continue
        avg = sum(a.intensity for a in chunk) / len(chunk)
        label = "peak" if avg >= 0.7 else "valley" if avg <= 0.3 else "mid"
        zones.append(
            EnergyZone(start=chunk[0].position, end=chunk[-1].position, avg_intensity=round(avg, 3), label=label)
        )
    return zones


def transition_density(artworks: list[Artwork]) -> TransitionMetrics:
    """Measure intensity jumps between consecutive artworks."""
    ordered = sorted(artworks, key=lambda a: a.position)
    if len(ordered) < 2:
        return TransitionMetrics(count=0, avg_delta=0.0, max_delta=0.0, density=0.0)
    deltas = [abs(ordered[i + 1].intensity - ordered[i].intensity) for i in range(len(ordered) - 1)]
    avg = sum(deltas) / len(deltas)
    max_d = max(deltas)
    density = min(1.0, avg / 0.5)
    return TransitionMetrics(
        count=len(deltas),
        avg_delta=round(avg, 3),
        max_delta=round(max_d, 3),
        density=round(density, 3),
    )


def pacing_score(artworks: list[Artwork]) -> float:
    """Score pacing balance: penalize flat or chaotic intensity curves."""
    ordered = sorted(artworks, key=lambda a: a.position)
    if len(ordered) < 2:
        return 50.0
    intensities = [a.intensity for a in ordered]
    mean = sum(intensities) / len(intensities)
    variance = sum((x - mean) ** 2 for x in intensities) / len(intensities)
    transitions = transition_density(ordered)
    # Sweet spot: moderate variance + moderate transition density
    var_score = 100.0 * math.exp(-((variance - 0.04) ** 2) / 0.02)
    trans_score = 100.0 * (1.0 - abs(transitions.density - 0.5))
    return max(0.0, min(100.0, 0.6 * var_score + 0.4 * trans_score))


def wall_text_craft(artworks: list[Artwork]) -> float:
    """Average wall text ratio mapped to craft score."""
    if not artworks:
        return 50.0
    avg = sum(a.wall_text_ratio for a in artworks) / len(artworks)
    # Optimal around 0.35
    return max(0.0, min(100.0, 100.0 - abs(avg - 0.35) * 200))


def build_craft_report(exhibition: Exhibition) -> CraftReport:
    arts = exhibition.all_artworks()
    trans = transition_density(arts)
    return CraftReport(
        pacing_score=round(pacing_score(arts), 2),
        wall_text_ratio=round(wall_text_craft(arts), 2),
        transition_density=trans.density,
        energy_zones=energy_map(arts),
    )
