"""Expanded energy maps with intensity gradients."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from vitrine_mix.craft import EnergyZone, energy_map
from vitrine_types.models import Artwork, Exhibition


@dataclass
class GradientPoint:
    position: int
    intensity: float
    gradient: float
    label: str


@dataclass
class EnergyGradientMap:
    points: list[GradientPoint]
    zones: list[EnergyZone]
    max_gradient: float
    min_gradient: float
    avg_intensity: float
    volatility: float


@dataclass
class EnergyProfile:
    exhibition_id: str
    gradient_map: EnergyGradientMap
    peak_positions: list[int]
    valley_positions: list[int]
    inflection_count: int
    recommendations: list[str] = field(default_factory=list)


def _compute_gradients(artworks: list[Artwork]) -> list[GradientPoint]:
    ordered = sorted(artworks, key=lambda a: a.position)
    points: list[GradientPoint] = []
    for i, art in enumerate(ordered):
        if i == 0:
            grad = 0.0
        else:
            prev = ordered[i - 1]
            grad = art.intensity - prev.intensity
        if grad > 0.15:
            label = "rising"
        elif grad < -0.15:
            label = "falling"
        else:
            label = "steady"
        points.append(
            GradientPoint(
                position=art.position,
                intensity=art.intensity,
                gradient=round(grad, 3),
                label=label,
            )
        )
    return points


def build_energy_gradient_map(
    artworks: list[Artwork],
    zone_size: int = 3,
) -> EnergyGradientMap:
    """Build energy map enriched with per-position gradients."""
    if not artworks:
        return EnergyGradientMap([], [], 0.0, 0.0, 0.0, 0.0)

    points = _compute_gradients(artworks)
    zones = energy_map(artworks, zone_size=zone_size)
    gradients = [p.gradient for p in points]
    intensities = [p.intensity for p in points]
    mean_int = sum(intensities) / len(intensities)
    variance = sum((x - mean_int) ** 2 for x in intensities) / len(intensities)

    return EnergyGradientMap(
        points=points,
        zones=zones,
        max_gradient=round(max(gradients), 3),
        min_gradient=round(min(gradients), 3),
        avg_intensity=round(mean_int, 3),
        volatility=round(math.sqrt(variance), 3),
    )


def analyze_energy_profile(exhibition: Exhibition, zone_size: int = 3) -> EnergyProfile:
    """Full energy profile with peaks, valleys, and recommendations."""
    arts = exhibition.all_artworks()
    grad_map = build_energy_gradient_map(arts, zone_size=zone_size)

    peaks: list[int] = []
    valleys: list[int] = []
    inflections = 0

    for i, pt in enumerate(grad_map.points):
        if i > 0 and i < len(grad_map.points) - 1:
            prev_g = grad_map.points[i - 1].gradient
            next_g = grad_map.points[i + 1].gradient if i + 1 < len(grad_map.points) else 0
            if prev_g > 0 and next_g < 0:
                peaks.append(pt.position)
            if prev_g < 0 and next_g > 0:
                valleys.append(pt.position)
            if (prev_g > 0) != (pt.gradient > 0):
                inflections += 1

        if pt.intensity >= 0.75:
            peaks.append(pt.position)
        elif pt.intensity <= 0.25:
            valleys.append(pt.position)

    peaks = sorted(set(peaks))
    valleys = sorted(set(valleys))

    recs: list[str] = []
    if grad_map.volatility > 0.25:
        recs.append("High energy volatility — consider buffer works between sharp transitions")
    if len(peaks) == 0:
        recs.append("No intensity peaks detected — add a focal work in the middle third")
    if len(valleys) < 2:
        recs.append("Add rest zones with lower intensity for visitor recovery")
    if abs(grad_map.max_gradient) > 0.4:
        recs.append(f"Max gradient {grad_map.max_gradient:.2f} may cause visitor fatigue")
    if not recs:
        recs.append("Energy profile within recommended bounds")

    return EnergyProfile(
        exhibition_id=exhibition.id,
        gradient_map=grad_map,
        peak_positions=peaks,
        valley_positions=valleys,
        inflection_count=inflections,
        recommendations=recs,
    )


def gradient_heatmap_rows(profile: EnergyProfile) -> list[dict[str, object]]:
    return [
        {
            "position": p.position,
            "intensity": p.intensity,
            "gradient": p.gradient,
            "label": p.label,
        }
        for p in profile.gradient_map.points
    ]


def zone_transition_summary(profile: EnergyProfile) -> list[dict[str, object]]:
    zones = profile.gradient_map.zones
    summary: list[dict[str, object]] = []
    for i in range(len(zones) - 1):
        delta = zones[i + 1].avg_intensity - zones[i].avg_intensity
        summary.append(
            {
                "from_zone": zones[i].label,
                "to_zone": zones[i + 1].label,
                "intensity_delta": round(delta, 3),
            }
        )
    return summary


def compare_energy_profiles(a: EnergyProfile, b: EnergyProfile) -> dict[str, float]:
    return {
        "volatility_delta": round(a.gradient_map.volatility - b.gradient_map.volatility, 3),
        "peak_count_delta": float(len(a.peak_positions) - len(b.peak_positions)),
        "avg_intensity_delta": round(
            a.gradient_map.avg_intensity - b.gradient_map.avg_intensity, 3
        ),
    }


def smoothness_score(profile: EnergyProfile) -> float:
    """Higher score = smoother energy flow."""
    gm = profile.gradient_map
    if not gm.points:
        return 50.0
    avg_abs_grad = sum(abs(p.gradient) for p in gm.points) / len(gm.points)
    return round(max(0.0, min(100.0, 100.0 * (1.0 - avg_abs_grad / 0.5))), 2)
