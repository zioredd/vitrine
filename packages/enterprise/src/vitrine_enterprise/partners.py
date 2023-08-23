"""Partner SLA tracking and breach detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Iterable

from vitrine_enterprise.program import PartnerOps


class SLAStatus(str, Enum):
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    UNKNOWN = "unknown"


@dataclass
class SLAMetric:
    name: str
    target: float
    actual: float
    unit: str = "ratio"

    @property
    def compliance(self) -> float:
        if self.target <= 0:
            return 1.0
        return min(1.0, self.actual / self.target)

    @property
    def gap(self) -> float:
        return self.target - self.actual


@dataclass
class PartnerSLARecord:
    partner_id: str
    partner_name: str
    metrics: list[SLAMetric]
    overall_compliance: float
    status: SLAStatus
    active_exhibitions: int
    breach_count: int
    last_review: date | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class SLAPortfolioReport:
    partners: list[PartnerSLARecord]
    portfolio_compliance: float
    at_risk_count: int
    breached_count: int
    top_performers: list[str]
    action_items: list[str] = field(default_factory=list)


DEFAULT_SLA_TARGETS: dict[str, float] = {
    "uptime": 0.995,
    "response_time_hours": 4.0,
    "delivery_on_time": 0.95,
    "data_quality": 0.90,
    "incident_resolution_days": 3.0,
}


def evaluate_partner_sla(
    partner: PartnerOps,
    metrics: list[SLAMetric] | None = None,
    *,
    at_risk_threshold: float = 0.85,
    breach_threshold: float = 0.70,
) -> PartnerSLARecord:
    """Evaluate SLA compliance for a single partner."""
    if metrics is None:
        metrics = [
            SLAMetric("uptime", DEFAULT_SLA_TARGETS["uptime"], partner.sla_compliance),
            SLAMetric("data_quality", DEFAULT_SLA_TARGETS["data_quality"], partner.sla_compliance * 0.98),
            SLAMetric("delivery_on_time", DEFAULT_SLA_TARGETS["delivery_on_time"], partner.sla_compliance * 0.95),
        ]

    compliances = [m.compliance for m in metrics]
    overall = sum(compliances) / len(compliances) if compliances else partner.sla_compliance
    breaches = sum(1 for m in metrics if m.compliance < breach_threshold)

    if overall < breach_threshold or breaches >= 2:
        status = SLAStatus.BREACHED
    elif overall < at_risk_threshold or partner.at_risk():
        status = SLAStatus.AT_RISK
    elif overall >= at_risk_threshold:
        status = SLAStatus.COMPLIANT
    else:
        status = SLAStatus.UNKNOWN

    notes: list[str] = []
    for m in metrics:
        if m.compliance < breach_threshold:
            notes.append(f"{m.name} breach: {m.actual:.2f} vs target {m.target:.2f}")

    return PartnerSLARecord(
        partner_id=partner.partner_id,
        partner_name=partner.name,
        metrics=metrics,
        overall_compliance=round(overall, 3),
        status=status,
        active_exhibitions=partner.active_exhibitions,
        breach_count=breaches,
        notes=notes,
    )


def build_sla_portfolio(
    partners: Iterable[PartnerOps],
    custom_metrics: dict[str, list[SLAMetric]] | None = None,
) -> SLAPortfolioReport:
    """Build portfolio-wide SLA report across partners."""
    records: list[PartnerSLARecord] = []
    custom_metrics = custom_metrics or {}

    for partner in partners:
        metrics = custom_metrics.get(partner.partner_id)
        records.append(evaluate_partner_sla(partner, metrics))

    if not records:
        return SLAPortfolioReport([], 1.0, 0, 0, [], [])

    portfolio = sum(r.overall_compliance for r in records) / len(records)
    at_risk = sum(1 for r in records if r.status == SLAStatus.AT_RISK)
    breached = sum(1 for r in records if r.status == SLAStatus.BREACHED)
    top = sorted(records, key=lambda r: -r.overall_compliance)[:3]

    actions: list[str] = []
    for r in records:
        if r.status == SLAStatus.BREACHED:
            actions.append(f"Initiate remediation plan for {r.partner_name}")
        elif r.status == SLAStatus.AT_RISK:
            actions.append(f"Schedule QBR with {r.partner_name}")

    return SLAPortfolioReport(
        partners=records,
        portfolio_compliance=round(portfolio, 3),
        at_risk_count=at_risk,
        breached_count=breached,
        top_performers=[r.partner_name for r in top],
        action_items=actions,
    )


def rolling_sla_compliance(
    history: list[tuple[date, float]],
    window: int = 3,
) -> list[tuple[date, float]]:
    """Compute rolling average SLA compliance over review periods."""
    if not history:
        return []
    result: list[tuple[date, float]] = []
    for i in range(window - 1, len(history)):
        window_slice = history[i - window + 1 : i + 1]
        avg = sum(h[1] for h in window_slice) / len(window_slice)
        result.append((window_slice[-1][0], round(avg, 3)))
    return result


def sla_breach_forecast(
    record: PartnerSLARecord,
    trend_slope: float,
    days_ahead: int = 30,
) -> dict[str, object]:
    """Project SLA compliance forward using linear trend."""
    projected = record.overall_compliance + trend_slope * days_ahead
    projected = max(0.0, min(1.0, projected))
    will_breach = projected < DEFAULT_SLA_TARGETS.get("data_quality", 0.9) * 0.78
    return {
        "partner_id": record.partner_id,
        "current": record.overall_compliance,
        "projected": round(projected, 3),
        "days_ahead": days_ahead,
        "breach_likely": will_breach,
    }


def partner_scorecard(record: PartnerSLARecord) -> dict[str, object]:
    return {
        "partner_id": record.partner_id,
        "name": record.partner_name,
        "grade": _compliance_grade(record.overall_compliance),
        "status": record.status.value,
        "metrics": [
            {"name": m.name, "target": m.target, "actual": m.actual, "compliance": round(m.compliance, 3)}
            for m in record.metrics
        ],
        "active_exhibitions": record.active_exhibitions,
        "notes": record.notes,
    }


def _compliance_grade(compliance: float) -> str:
    if compliance >= 0.95:
        return "A"
    if compliance >= 0.85:
        return "B"
    if compliance >= 0.75:
        return "C"
    if compliance >= 0.65:
        return "D"
    return "F"


def days_since_review(record: PartnerSLARecord, reference: date | None = None) -> int | None:
    if record.last_review is None:
        return None
    ref = reference or date.today()
    return (ref - record.last_review).days


def stale_review_partners(
    records: Iterable[PartnerSLARecord],
    max_days: int = 90,
    reference: date | None = None,
) -> list[str]:
    ref = reference or date.today()
    stale: list[str] = []
    for r in records:
        if r.last_review is None or (ref - r.last_review).days > max_days:
            stale.append(r.partner_id)
    return stale
