"""Incident severity scoring and escalation logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import IntEnum
from typing import Iterable

from vitrine_enterprise.program import Incident, IncidentResponse


class SeverityLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


SEVERITY_WEIGHTS: dict[str, float] = {
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}


@dataclass
class ScoringFactor:
    name: str
    weight: float
    value: float
    contribution: float


@dataclass
class IncidentScore:
    incident_id: str
    raw_severity: str
    numeric_score: float
    level: SeverityLevel
    factors: list[ScoringFactor]
    escalation_required: bool
    sla_breach: bool


@dataclass
class IncidentPortfolio:
    scores: list[IncidentScore]
    aggregate_risk: float
    open_critical: int
    mean_time_open_days: float
    recommendations: list[str] = field(default_factory=list)


def _parse_severity(severity: str) -> SeverityLevel:
    mapping = {
        "low": SeverityLevel.LOW,
        "medium": SeverityLevel.MEDIUM,
        "high": SeverityLevel.HIGH,
        "critical": SeverityLevel.CRITICAL,
    }
    return mapping.get(severity.lower(), SeverityLevel.MEDIUM)


def score_incident(
    incident: Incident,
    *,
    reference: date | None = None,
    sla_days: dict[str, int] | None = None,
    impact_multiplier: float = 1.0,
) -> IncidentScore:
    """Compute composite severity score for a single incident."""
    ref = reference or date.today()
    sla = sla_days or {"low": 30, "medium": 14, "high": 7, "critical": 1}
    level = _parse_severity(incident.severity)
    base = SEVERITY_WEIGHTS.get(incident.severity.lower(), 0.5)

    factors: list[ScoringFactor] = []
    factors.append(
        ScoringFactor("base_severity", 0.4, base, round(0.4 * base, 3))
    )

    age_days = (ref - incident.opened_on).days if not incident.resolved else 0
    age_factor = min(1.0, age_days / 30.0)
    factors.append(
        ScoringFactor("age", 0.2, age_factor, round(0.2 * age_factor, 3))
    )

    open_penalty = 0.0 if incident.resolved else 0.15
    factors.append(
        ScoringFactor("open_status", 0.15, 1.0 if not incident.resolved else 0.0, open_penalty)
    )

    summary_len = len(incident.summary.split())
    detail_factor = min(1.0, summary_len / 20.0)
    factors.append(
        ScoringFactor("detail", 0.1, detail_factor, round(0.1 * detail_factor, 3))
    )

    impact = min(1.0, impact_multiplier)
    factors.append(
        ScoringFactor("impact", 0.15, impact, round(0.15 * impact, 3))
    )

    numeric = sum(f.contribution for f in factors)
    numeric = round(min(1.0, numeric), 3)

    sla_limit = sla.get(incident.severity.lower(), 14)
    sla_breach = not incident.resolved and age_days > sla_limit
    escalation = level >= SeverityLevel.HIGH or sla_breach or numeric >= 0.75

    return IncidentScore(
        incident_id=incident.id,
        raw_severity=incident.severity,
        numeric_score=numeric,
        level=level,
        factors=factors,
        escalation_required=escalation,
        sla_breach=sla_breach,
    )


def score_portfolio(
    response: IncidentResponse,
    reference: date | None = None,
) -> IncidentPortfolio:
    """Score all incidents and produce portfolio-level metrics."""
    ref = reference or date.today()
    open_incidents = [i for i in response.incidents if not i.resolved]
    scores = [score_incident(i, reference=ref) for i in response.incidents]

    if not scores:
        return IncidentPortfolio(scores=[], aggregate_risk=0.0, open_critical=0, mean_time_open_days=0.0)

    aggregate = sum(s.numeric_score for s in scores) / len(scores)
    critical = sum(1 for s in scores if s.level == SeverityLevel.CRITICAL and not any(
        i.resolved for i in response.incidents if i.id == s.incident_id
    ))
    ages = [(ref - i.opened_on).days for i in open_incidents]
    mean_age = sum(ages) / len(ages) if ages else 0.0

    recs: list[str] = []
    if critical > 0:
        recs.append(f"Address {critical} critical open incident(s) immediately")
    sla_breaches = sum(1 for s in scores if s.sla_breach)
    if sla_breaches:
        recs.append(f"{sla_breaches} incident(s) exceed SLA — escalate to on-call")
    if aggregate > 0.6:
        recs.append("Portfolio risk elevated — schedule incident review board")

    return IncidentPortfolio(
        scores=scores,
        aggregate_risk=round(aggregate, 3),
        open_critical=critical,
        mean_time_open_days=round(mean_age, 1),
        recommendations=recs,
    )


def rank_incidents(incidents: Iterable[Incident], reference: date | None = None) -> list[IncidentScore]:
    return sorted(
        [score_incident(i, reference=reference) for i in incidents],
        key=lambda s: (-s.numeric_score, -s.level),
    )


def suggest_escalation_path(score: IncidentScore) -> list[str]:
    steps: list[str] = []
    if score.level >= SeverityLevel.CRITICAL:
        steps.extend(["notify_executive", "activate_war_room", "page_on_call"])
    elif score.level >= SeverityLevel.HIGH:
        steps.extend(["notify_manager", "assign_incident_commander"])
    elif score.sla_breach:
        steps.append("escalate_to_tier2")
    else:
        steps.append("standard_triage")
    return steps


def incident_trend(
    incidents: list[Incident],
    window_days: int = 90,
    reference: date | None = None,
) -> dict[str, float]:
    ref = reference or date.today()
    cutoff = ref - timedelta(days=window_days)
    recent = [i for i in incidents if i.opened_on >= cutoff]
    if not recent:
        return {"count": 0.0, "critical_rate": 0.0, "resolution_rate": 0.0}
    resolved = sum(1 for i in recent if i.resolved)
    critical = sum(1 for i in recent if i.severity.lower() == "critical")
    return {
        "count": float(len(recent)),
        "critical_rate": round(critical / len(recent), 3),
        "resolution_rate": round(resolved / len(recent), 3),
    }
