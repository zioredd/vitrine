"""Editorial analytics: booking risks, release windows, royalty tiers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from vitrine_types.models import Exhibition


@dataclass
class BookingRisk:
    exhibition_id: str
    risk_score: float
    factors: list[str]


@dataclass
class ReleaseWindow:
    exhibition_id: str
    start: date
    end: date
    conflict_level: float


@dataclass
class RoyaltyTier:
    tier: str
    share_pct: float
    min_score: float


ROYALTY_TIERS = [
    RoyaltyTier(tier="platinum", share_pct=0.35, min_score=90.0),
    RoyaltyTier(tier="gold", share_pct=0.25, min_score=75.0),
    RoyaltyTier(tier="silver", share_pct=0.15, min_score=60.0),
    RoyaltyTier(tier="bronze", share_pct=0.08, min_score=0.0),
]


def assess_booking_risks(exhibitions: list[Exhibition]) -> list[BookingRisk]:
    results: list[BookingRisk] = []
    for ex in exhibitions:
        factors: list[str] = []
        risk = 0.0
        if len(ex.all_artworks()) < 5:
            risk += 0.25
            factors.append("sparse catalog")
        low_conf = sum(1 for s in ex.signals if s.provenance.confidence < 0.6)
        if low_conf:
            risk += min(0.4, 0.1 * low_conf)
            factors.append("weak provenance")
        if ex.crowd_score is not None and ex.crowd_score < 40:
            risk += 0.2
            factors.append("low crowd score")
        results.append(BookingRisk(exhibition_id=ex.id, risk_score=min(1.0, risk), factors=factors))
    return results


def compute_release_windows(exhibitions: list[Exhibition], horizon_days: int = 90) -> list[ReleaseWindow]:
    today = date.today()
    windows: list[ReleaseWindow] = []
    for ex in exhibitions:
        start = ex.opened_on or today
        end = ex.closed_on or (start + timedelta(days=horizon_days))
        overlap = sum(
            1
            for other in exhibitions
            if other.id != ex.id and other.opened_on and start <= other.opened_on <= end
        )
        conflict = min(1.0, overlap * 0.2)
        windows.append(ReleaseWindow(exhibition_id=ex.id, start=start, end=end, conflict_level=conflict))
    return windows


def resolve_royalty_tier(vitrine_score: float) -> RoyaltyTier:
    for tier in ROYALTY_TIERS:
        if vitrine_score >= tier.min_score:
            return tier
    return ROYALTY_TIERS[-1]
