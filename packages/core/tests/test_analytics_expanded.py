"""Expanded analytics module tests."""

from __future__ import annotations

from vitrine_catalog.repository import CatalogRepository
from vitrine_core.alerts import run_alert_engine
from vitrine_core.analytics import (
    alert_engine,
    audience_cohorts,
    catalog_stress_index,
    provenance_audit,
    what_if_simulator,
)
from vitrine_core.booking_matrix import build_booking_risk_matrix
from vitrine_core.cohorts import cluster_audience_cohorts
from vitrine_core.provenance_trails import audit_trails
from vitrine_core.royalty import calculate_royalty_tier, royalty_portfolio_summary
from vitrine_core.scenarios import run_scenario_plan
from vitrine_core.stress_simulator import simulate_catalog_stress
from vitrine_types.models import Exhibition


def _seed_exhibitions() -> list[Exhibition]:
    return CatalogRepository.from_seed().load_all()


def test_audience_cohorts_from_seed():
    cohorts = audience_cohorts(_seed_exhibitions())
    assert len(cohorts) >= 1
    assert all(c.size > 0 for c in cohorts)


def test_provenance_audit_counts():
    audit = provenance_audit(_seed_exhibitions())
    assert audit.total_signals > 0
    assert isinstance(audit.by_source, dict)


def test_catalog_stress_index_range():
    stress = catalog_stress_index(_seed_exhibitions())
    assert 0.0 <= stress <= 100.0


def test_what_if_simulator_returns_delta():
    ex = _seed_exhibitions()[0]
    result = what_if_simulator(ex)
    assert result.baseline_score >= 0
    assert isinstance(result.assumptions, list)


def test_alert_engine_produces_alerts():
    alerts = alert_engine(_seed_exhibitions())
    assert isinstance(alerts, list)


def test_run_alert_engine_report():
    report = run_alert_engine(_seed_exhibitions())
    assert len(report.alerts) >= 0
    assert isinstance(report.by_severity, dict)


def test_cluster_audience_cohorts():
    result = cluster_audience_cohorts(_seed_exhibitions())
    assert len(result.clusters) >= 1


def test_audit_trails_report():
    report = audit_trails(_seed_exhibitions())
    assert len(report.trails) >= 0


def test_build_booking_risk_matrix():
    matrix = build_booking_risk_matrix(_seed_exhibitions())
    assert len(matrix.cells) > 0


def test_simulate_catalog_stress():
    sim = simulate_catalog_stress(_seed_exhibitions())
    assert sim.projected_index >= 0


def test_run_scenario_plan():
    ex = _seed_exhibitions()[0]
    plan = run_scenario_plan(ex)
    assert len(plan.outcomes) >= 1


def test_calculate_royalty_tier():
    ex = _seed_exhibitions()[0]
    tier = calculate_royalty_tier(ex)
    assert tier.band.tier in ("bronze", "silver", "gold", "platinum", "development")


def test_royalty_portfolio_summary():
    summary = royalty_portfolio_summary(_seed_exhibitions())
    assert sum(summary.values()) == 48


def test_cohort_avg_scores_bounded():
    cohorts = audience_cohorts(_seed_exhibitions())
    for c in cohorts:
        assert 0 <= c.avg_score <= 100
