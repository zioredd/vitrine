"""Royalty tier calculator with multi-factor scoring bands."""

from __future__ import annotations

from dataclasses import dataclass

from vitrine_types.models import Exhibition


@dataclass
class RoyaltyBand:
    tier: str
    share_pct: float
    min_composite: float
    perks: list[str]


@dataclass
class RoyaltyCalculation:
    exhibition_id: str
    composite_score: float
    band: RoyaltyBand
    signal_component: float
    craft_component: float
    crowd_component: float
    uplift_pct: float


ROYALTY_BANDS: list[RoyaltyBand] = [
    RoyaltyBand("platinum", 0.35, 90.0, ["priority booking", "co-marketing", "extended run"]),
    RoyaltyBand("gold", 0.25, 75.0, ["featured placement", "press support"]),
    RoyaltyBand("silver", 0.15, 60.0, ["standard placement"]),
    RoyaltyBand("bronze", 0.08, 45.0, ["emerging artist rate"]),
    RoyaltyBand("development", 0.04, 0.0, ["incubator program"]),
]


def _craft_proxy(ex: Exhibition) -> float:
    arts = ex.all_artworks()
    if not arts:
        return 50.0
    avg_int = sum(a.intensity for a in arts) / len(arts)
    avg_dwell = sum(a.dwell_sec for a in arts) / len(arts)
    dwell_score = min(100.0, avg_dwell / 3.0)
    return (avg_int * 100 + dwell_score) / 2


def calculate_royalty_tier(ex: Exhibition) -> RoyaltyCalculation:
    signal_scores = [s.score for s in ex.signals]
    signal_component = sum(signal_scores) / len(signal_scores) if signal_scores else 50.0
    craft_component = _craft_proxy(ex)
    crowd_component = ex.crowd_score or 50.0
    vitrine = ex.vitrine_score

    if vitrine is not None:
        composite = vitrine
    else:
        composite = 0.4 * signal_component + 0.35 * craft_component + 0.25 * crowd_component

    band = ROYALTY_BANDS[-1]
    for candidate in ROYALTY_BANDS:
        if composite >= candidate.min_composite:
            band = candidate
            break

    next_band_idx = max(0, ROYALTY_BANDS.index(band) - 1)
    next_threshold = ROYALTY_BANDS[next_band_idx].min_composite if next_band_idx < len(ROYALTY_BANDS) else 100.0
    uplift = max(0.0, next_threshold - composite) if band.tier != "platinum" else 0.0

    return RoyaltyCalculation(
        exhibition_id=ex.id,
        composite_score=round(composite, 2),
        band=band,
        signal_component=round(signal_component, 2),
        craft_component=round(craft_component, 2),
        crowd_component=round(crowd_component, 2),
        uplift_pct=round(uplift, 2),
    )


def royalty_portfolio_summary(exhibitions: list[Exhibition]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ex in exhibitions:
        calc = calculate_royalty_tier(ex)
        counts[calc.band.tier] = counts.get(calc.band.tier, 0) + 1
    return counts


def projected_royalty_revenue(
    exhibitions: list[Exhibition],
    base_revenue: float = 1_000_000.0,
) -> dict[str, float]:
    """Allocate revenue pool by tier share weighted by exhibition count."""
    calcs = [calculate_royalty_tier(ex) for ex in exhibitions]
    if not calcs:
        return {}
    total_weight = sum(c.band.share_pct for c in calcs)
    by_tier: dict[str, float] = {}
    for calc in calcs:
        share = (calc.band.share_pct / total_weight) * base_revenue if total_weight else 0.0
        by_tier[calc.band.tier] = by_tier.get(calc.band.tier, 0.0) + share
    return {k: round(v, 2) for k, v in by_tier.items()}
