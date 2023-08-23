"""Enterprise modules: executive program, budget, compliance, incidents, board pack."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from vitrine_core.intelligence import build_intelligence_report
from vitrine_types.models import Exhibition


@dataclass
class ExecutiveProgram:
    name: str
    sponsor: str
    exhibitions: list[str] = field(default_factory=list)
    budget_allocated: float = 0.0
    budget_spent: float = 0.0

    @property
    def utilization(self) -> float:
        if self.budget_allocated <= 0:
            return 0.0
        return min(1.0, self.budget_spent / self.budget_allocated)


@dataclass
class BudgetLine:
    category: str
    planned: float
    actual: float

    @property
    def variance(self) -> float:
        return self.actual - self.planned


@dataclass
class BudgetOffice:
    fiscal_year: int
    lines: list[BudgetLine] = field(default_factory=list)

    def total_variance(self) -> float:
        return sum(line.variance for line in self.lines)

    def overspend_categories(self) -> list[str]:
        return [line.category for line in self.lines if line.variance > 0]


@dataclass
class PartnerOps:
    partner_id: str
    name: str
    active_exhibitions: int = 0
    sla_compliance: float = 1.0

    def at_risk(self) -> bool:
        return self.sla_compliance < 0.85


@dataclass
class ComplianceCheck:
    regulation: str
    passed: bool
    notes: str = ""


@dataclass
class ComplianceReport:
    checks: list[ComplianceCheck]

    @property
    def pass_rate(self) -> float:
        if not self.checks:
            return 1.0
        return sum(1 for c in self.checks if c.passed) / len(self.checks)


@dataclass
class DataContract:
    name: str
    schema_version: str
    required_fields: list[str]
    owner: str


@dataclass
class Incident:
    id: str
    severity: str
    summary: str
    opened_on: date
    resolved: bool = False


@dataclass
class IncidentResponse:
    incidents: list[Incident] = field(default_factory=list)

    def open_count(self) -> int:
        return sum(1 for i in self.incidents if not i.resolved)

    def critical_open(self) -> list[Incident]:
        return [i for i in self.incidents if not i.resolved and i.severity == "critical"]


@dataclass
class BoardPack:
    period: str
    executive_summary: str
    kpis: dict[str, float]
    programs: list[ExecutiveProgram]
    compliance: ComplianceReport
    incidents: IncidentResponse


def build_board_pack(
    exhibitions: list[Exhibition],
    programs: list[ExecutiveProgram],
    compliance: ComplianceReport,
    incidents: IncidentResponse,
    period: str = "Q2 2026",
) -> BoardPack:
    intel = build_intelligence_report(exhibitions, alerts=[])
    kpis = {
        "exhibition_count": float(intel.exhibition_count),
        "avg_vitrine_score": intel.avg_vitrine_score,
        "catalog_stress": intel.catalog_stress_index,
        "open_incidents": float(incidents.open_count()),
        "compliance_pass_rate": compliance.pass_rate,
    }
    summary = (
        f"{intel.exhibition_count} exhibitions tracked; "
        f"avg score {intel.avg_vitrine_score:.1f}; "
        f"{incidents.open_count()} open incidents."
    )
    return BoardPack(
        period=period,
        executive_summary=summary,
        kpis=kpis,
        programs=programs,
        compliance=compliance,
        incidents=incidents,
    )


def validate_data_contract(record: dict, contract: DataContract) -> list[str]:
    missing = [f for f in contract.required_fields if f not in record]
    return missing
