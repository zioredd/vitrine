from datetime import date

from vitrine_types.models import Exhibition

from vitrine_enterprise.program import (
    BoardPack,
    BudgetLine,
    BudgetOffice,
    ComplianceCheck,
    ComplianceReport,
    DataContract,
    ExecutiveProgram,
    Incident,
    IncidentResponse,
    PartnerOps,
    build_board_pack,
    validate_data_contract,
)


def test_executive_program_utilization():
    prog = ExecutiveProgram(name="Modern", sponsor="CEO", budget_allocated=100_000, budget_spent=75_000)
    assert prog.utilization == 0.75


def test_budget_office_variance():
    office = BudgetOffice(
        fiscal_year=2026,
        lines=[
            BudgetLine(category="install", planned=50_000, actual=55_000),
            BudgetLine(category="marketing", planned=20_000, actual=18_000),
        ],
    )
    assert office.total_variance() == 3_000
    assert "install" in office.overspend_categories()


def test_partner_ops_at_risk():
    partner = PartnerOps(partner_id="p1", name="Gallery X", sla_compliance=0.7)
    assert partner.at_risk()


def test_compliance_pass_rate():
    report = ComplianceReport(
        checks=[
            ComplianceCheck(regulation="GDPR", passed=True),
            ComplianceCheck(regulation="SOC2", passed=False),
        ]
    )
    assert report.pass_rate == 0.5


def test_incident_response():
    ir = IncidentResponse(
        incidents=[
            Incident(id="i1", severity="critical", summary="Outage", opened_on=date.today()),
            Incident(id="i2", severity="low", summary="Typo", opened_on=date.today(), resolved=True),
        ]
    )
    assert ir.open_count() == 1
    assert len(ir.critical_open()) == 1


def test_build_board_pack():
    exs = [Exhibition(id="1", title="Show", curator="C", vitrine_score=80)]
    programs = [ExecutiveProgram(name="Flagship", sponsor="Board")]
    compliance = ComplianceReport(checks=[ComplianceCheck(regulation="GDPR", passed=True)])
    incidents = IncidentResponse()
    pack = build_board_pack(exs, programs, compliance, incidents)
    assert isinstance(pack, BoardPack)
    assert pack.kpis["exhibition_count"] == 1.0


def test_validate_data_contract():
    contract = DataContract(name="exhibition", schema_version="1", required_fields=["id", "title"], owner="data")
    missing = validate_data_contract({"id": "1"}, contract)
    assert missing == ["title"]
