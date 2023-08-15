"""Pluggable data-quality rule engine."""

from __future__ import annotations

from collections import Counter
from typing import Callable

from vitrine_mix.craft import build_craft_report, pacing_score
from vitrine_rules.models import RuleCheck, RuleResult, RuleViolation
from vitrine_types.models import Exhibition, Severity, Signal


def check_mix_range(exhibition: Exhibition, low: float = 30.0, high: float = 95.0) -> list[RuleViolation]:
    report = build_craft_report(exhibition)
    if report.pacing_score < low or report.pacing_score > high:
        return [
            RuleViolation(
                rule="mix_range",
                message=f"pacing score {report.pacing_score} outside [{low}, {high}]",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        ]
    return []


def check_intensity_range(exhibition: Exhibition) -> list[RuleViolation]:
    arts = exhibition.all_artworks()
    if not arts:
        return []
    for art in arts:
        if art.intensity < 0.05 or art.intensity > 0.98:
            return [
                RuleViolation(
                    rule="intensity_range",
                    message=f"artwork {art.id} intensity {art.intensity} out of range",
                    severity=Severity.ERROR,
                    exhibition_id=exhibition.id,
                )
            ]
    return []


def check_rank_consistency(exhibition: Exhibition) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    ranks = [s.provenance.rank for s in exhibition.signals if s.provenance.rank is not None]
    if ranks and ranks != sorted(ranks):
        violations.append(
            RuleViolation(
                rule="rank_consistency",
                message="provenance ranks not monotonic",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )
    return violations


def check_provenance_confidence(exhibition: Exhibition, min_conf: float = 0.4) -> list[RuleViolation]:
    violations: list[RuleViolation] = []
    for sig in exhibition.signals:
        if sig.provenance.confidence < min_conf:
            violations.append(
                RuleViolation(
                    rule="provenance_confidence",
                    message=f"signal {sig.id} confidence {sig.provenance.confidence} below {min_conf}",
                    severity=Severity.WARN,
                    exhibition_id=exhibition.id,
                )
            )
        if not sig.provenance.source_url:
            violations.append(
                RuleViolation(
                    rule="provenance_url",
                    message=f"signal {sig.id} missing source URL",
                    severity=Severity.INFO,
                    exhibition_id=exhibition.id,
                )
            )
    return violations


def check_signal_balance(exhibition: Exhibition) -> list[RuleViolation]:
    if len(exhibition.signals) < 2:
        return [
            RuleViolation(
                rule="signal_balance",
                message="fewer than 2 signals",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        ]
    kinds = {s.kind for s in exhibition.signals}
    if len(kinds) < 2:
        return [
            RuleViolation(
                rule="signal_balance",
                message="signals lack kind diversity",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        ]
    return []


def check_craft_balance(exhibition: Exhibition) -> list[RuleViolation]:
    score = pacing_score(exhibition.all_artworks())
    if score < 20:
        return [
            RuleViolation(
                rule="craft_balance",
                message=f"low craft pacing score {score}",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        ]
    return []


def check_title_identity(exhibition: Exhibition) -> list[RuleViolation]:
    if not exhibition.title or len(exhibition.title.strip()) < 3:
        return [
            RuleViolation(
                rule="title_identity",
                message="title too short or missing",
                severity=Severity.ERROR,
                exhibition_id=exhibition.id,
            )
        ]
    return []


def _extended_rules() -> list[RuleCheck]:
    from vitrine_rules.checks_extended import (
        check_date_range,
        check_graph_connectivity,
        check_signal_freshness,
        check_tag_density,
        check_venue_consistency,
    )

    return [
        check_venue_consistency,
        check_date_range,
        check_tag_density,
        check_graph_connectivity,
        check_signal_freshness,
    ]


DEFAULT_RULES: list[RuleCheck] = [
    check_mix_range,
    check_intensity_range,
    check_rank_consistency,
    check_provenance_confidence,
    check_signal_balance,
    check_craft_balance,
    check_title_identity,
    *_extended_rules(),
]


def run_rules(
    exhibitions: list[Exhibition],
    rules: list[RuleCheck] | None = None,
) -> RuleResult:
    rules = rules or DEFAULT_RULES
    violations: list[RuleViolation] = []
    for ex in exhibitions:
        for rule in rules:
            violations.extend(rule(ex))
    counts = Counter(v.severity.value for v in violations)
    return RuleResult(violations=violations, severity_counts=dict(counts))
