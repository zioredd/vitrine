"""Expanded enterprise module tests."""

from __future__ import annotations

from datetime import date

from vitrine_catalog.repository import CatalogRepository
from vitrine_enterprise.board_pack_gen import generate_expanded_board_pack
from vitrine_enterprise.compliance_matrix import assess_readiness, build_compliance_matrix
from vitrine_enterprise.forecasting import forecast_budget_office, forecast_category
from vitrine_enterprise.incidents import score_incident, score_portfolio
from vitrine_enterprise.partners import build_sla_portfolio, evaluate_partner_sla
from vitrine_enterprise.program import (
    BudgetLine,
    BudgetOffice,
    ComplianceCheck,
    ComplianceReport,
    ExecutiveProgram,
    Incident,
    IncidentResponse,
    PartnerOps,
)


def test_forecast_category_trend():
    history = [("Q1", 100, 95), ("Q2", 200, 190), ("Q3", 300, 310), ("Q4", 400, 420)]
    fc = forecast_category("curation", history)
    assert fc.projected_next > 0
    assert 0 <= fc.confidence <= 1


def test_forecast_budget_office():
    office = BudgetOffice(
        fiscal_year=2026,
        lines=[
            BudgetLine(category="curation", planned=100_000, actual=95_000),
            BudgetLine(category="install", planned=50_000, actual=55_000),
        ],
    )
    forecast = forecast_budget_office(office)
    assert forecast.total_planned == 150_000
    assert forecast.narrative


def test_compliance_matrix_build():
    checks = [
        ComplianceCheck(regulation="GDPR", passed=True),
        ComplianceCheck(regulation="SOC2", passed=False),
    ]
    matrix = build_compliance_matrix(checks)
    assert matrix.overall_score >= 0
    assert len(matrix.cells) > 0


def test_assess_readiness():
    matrix = build_compliance_matrix([ComplianceCheck(regulation="GDPR", passed=True)])
    readiness = assess_readiness(matrix, threshold=0.5)
    assert "ready" in readiness


def test_score_incident_critical():
    inc = Incident(id="i1", severity="critical", summary="Outage", opened_on=date.today())
    score = score_incident(inc)
    assert score.escalation_required
    assert score.level.value == 4


def test_score_portfolio():
    response = IncidentResponse(
        incidents=[
            Incident(id="i1", severity="medium", summary="Issue", opened_on=date.today()),
        ]
    )
    portfolio = score_portfolio(response)
    assert portfolio.aggregate_risk >= 0


def test_evaluate_partner_sla():
    partner = PartnerOps(partner_id="p1", name="Gallery", sla_compliance=0.92)
    record = evaluate_partner_sla(partner)
    assert record.overall_compliance > 0


def test_build_sla_portfolio():
    partners = [
        PartnerOps(partner_id="p1", name="A", sla_compliance=0.95),
        PartnerOps(partner_id="p2", name="B", sla_compliance=0.70),
    ]
    report = build_sla_portfolio(partners)
    assert len(report.partners) == 2
    assert report.at_risk_count >= 1


def test_generate_expanded_board_pack():
    exhibitions = CatalogRepository.from_seed().load_all()[:5]
    programs = [ExecutiveProgram(name="Residency", sponsor="Board")]
    compliance = ComplianceReport(checks=[ComplianceCheck(regulation="GDPR", passed=True)])
    incidents = IncidentResponse()
    office = BudgetOffice(fiscal_year=2026, lines=[BudgetLine("ops", 1000, 900)])
    pack = generate_expanded_board_pack(
        exhibitions, programs, compliance, incidents, budget_office=office
    )
    assert len(pack.sections) >= 3
    assert pack.compliance_matrix is not None
