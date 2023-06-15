"""Alert engine with severity escalation and deduplication."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum

from vitrine_core.provenance_trails import audit_trails
from vitrine_core.stress_simulator import simulate_catalog_stress
from vitrine_types.models import Exhibition


class AlertSeverity(IntEnum):
    INFO = 1
    WARN = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class EscalatedAlert:
    code: str
    message: str
    severity: AlertSeverity
    exhibition_id: str | None = None
    escalation_level: int = 0
    related_codes: list[str] = field(default_factory=list)


@dataclass
class AlertReport:
    alerts: list[EscalatedAlert]
    by_severity: dict[str, int]
    escalated_count: int
    top_codes: list[tuple[str, int]]


_ESCALATION_RULES: dict[str, tuple[str, AlertSeverity]] = {
    "PROV_LOW": ("PROV_CRITICAL", AlertSeverity.CRITICAL),
    "CATALOG_STRESS": ("CATALOG_CRITICAL", AlertSeverity.CRITICAL),
    "SCORE_LOW": ("SCORE_CRITICAL", AlertSeverity.CRITICAL),
}


def _base_alerts(exhibitions: list[Exhibition]) -> list[EscalatedAlert]:
    alerts: list[EscalatedAlert] = []
    audit = audit_trails(exhibitions)
    if audit.incomplete_count > 0:
        alerts.append(
            EscalatedAlert(
                code="PROV_LOW",
                message=f"{audit.incomplete_count} exhibitions with incomplete provenance",
                severity=AlertSeverity.WARN,
            )
        )
    if audit.stale_signals:
        alerts.append(
            EscalatedAlert(
                code="PROV_STALE",
                message=f"{len(audit.stale_signals)} stale provenance signals",
                severity=AlertSeverity.ERROR,
            )
        )

    sim = simulate_catalog_stress(exhibitions)
    if sim.projected_index > 0.5:
        alerts.append(
            EscalatedAlert(
                code="CATALOG_STRESS",
                message=f"catalog stress index {sim.projected_index:.2f}",
                severity=AlertSeverity.ERROR,
            )
        )

    for ex in exhibitions:
        if ex.vitrine_score is not None and ex.vitrine_score < 30:
            alerts.append(
                EscalatedAlert(
                    code="SCORE_LOW",
                    message=f"{ex.title} below threshold ({ex.vitrine_score:.1f})",
                    severity=AlertSeverity.CRITICAL,
                    exhibition_id=ex.id,
                )
            )
        elif ex.vitrine_score is not None and ex.vitrine_score < 45:
            alerts.append(
                EscalatedAlert(
                    code="SCORE_LOW",
                    message=f"{ex.title} underperforming ({ex.vitrine_score:.1f})",
                    severity=AlertSeverity.WARN,
                    exhibition_id=ex.id,
                )
            )
    return alerts


def _escalate(alerts: list[EscalatedAlert]) -> list[EscalatedAlert]:
    code_counts: dict[str, int] = defaultdict(int)
    for alert in alerts:
        code_counts[alert.code] += 1

    escalated: list[EscalatedAlert] = list(alerts)
    for code, count in code_counts.items():
        if count >= 3 and code in _ESCALATION_RULES:
            new_code, new_sev = _ESCALATION_RULES[code]
            escalated.append(
                EscalatedAlert(
                    code=new_code,
                    message=f"Escalated: {count} instances of {code}",
                    severity=new_sev,
                    escalation_level=1,
                    related_codes=[code],
                )
            )
    return escalated


def run_alert_engine(exhibitions: list[Exhibition]) -> AlertReport:
    base = _base_alerts(exhibitions)
    all_alerts = _escalate(base)
    by_sev: dict[str, int] = defaultdict(int)
    code_counts: dict[str, int] = defaultdict(int)
    escalated_n = 0
    for alert in all_alerts:
        by_sev[alert.severity.name.lower()] += 1
        code_counts[alert.code] += 1
        if alert.escalation_level > 0:
            escalated_n += 1
    top = sorted(code_counts.items(), key=lambda x: -x[1])[:5]
    return AlertReport(
        alerts=sorted(all_alerts, key=lambda a: -a.severity),
        by_severity=dict(by_sev),
        escalated_count=escalated_n,
        top_codes=top,
    )


def filter_alerts_by_severity(
    report: AlertReport,
    min_severity: AlertSeverity,
) -> list[EscalatedAlert]:
    return [a for a in report.alerts if a.severity >= min_severity]
