"""Vitrine core: scoring, intelligence, editorial, analytics."""

from vitrine_core.analytics import (
    Alert,
    ProvenanceAudit,
    WhatIfResult,
    alert_engine,
    audience_cohorts,
    catalog_stress_index,
    provenance_audit,
    what_if_simulator,
)
from vitrine_core.editorial import (
    BookingRisk,
    ReleaseWindow,
    RoyaltyTier,
    assess_booking_risks,
    compute_release_windows,
    resolve_royalty_tier,
)
from vitrine_core.intelligence import (
    CommandCenterSnapshot,
    DecisionReport,
    IntelligenceReport,
    build_command_center,
    build_decision_report,
    build_intelligence_report,
)
from vitrine_core.scoring import (
    clamp,
    composite_vitrine_score,
    freshness_decay,
    rank_normalize,
    weighted_signal_blend,
)

__all__ = [
    "Alert",
    "BookingRisk",
    "CommandCenterSnapshot",
    "DecisionReport",
    "IntelligenceReport",
    "ProvenanceAudit",
    "ReleaseWindow",
    "RoyaltyTier",
    "WhatIfResult",
    "alert_engine",
    "assess_booking_risks",
    "audience_cohorts",
    "build_command_center",
    "build_decision_report",
    "build_intelligence_report",
    "catalog_stress_index",
    "clamp",
    "composite_vitrine_score",
    "compute_release_windows",
    "freshness_decay",
    "provenance_audit",
    "rank_normalize",
    "resolve_royalty_tier",
    "weighted_signal_blend",
    "what_if_simulator",
]
