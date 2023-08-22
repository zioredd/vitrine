"""Regulatory compliance matrices with cross-regulation scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from vitrine_enterprise.program import ComplianceCheck, ComplianceReport


class RegulationTier(str, Enum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    ADVISORY = "advisory"


@dataclass
class RegulationDefinition:
    code: str
    name: str
    tier: RegulationTier
    weight: float = 1.0
    domains: list[str] = field(default_factory=list)


@dataclass
class MatrixCell:
    regulation: str
    domain: str
    passed: bool
    score: float
    notes: str = ""


@dataclass
class ComplianceMatrix:
    domains: list[str]
    regulations: list[str]
    cells: list[MatrixCell]
    overall_score: float
    domain_scores: dict[str, float] = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)


DEFAULT_REGULATIONS: list[RegulationDefinition] = [
    RegulationDefinition("GDPR", "General Data Protection", RegulationTier.MANDATORY, 1.0, ["data", "privacy"]),
    RegulationDefinition("SOC2", "SOC 2 Type II", RegulationTier.MANDATORY, 0.9, ["security", "ops"]),
    RegulationDefinition("ADA", "Accessibility", RegulationTier.MANDATORY, 0.85, ["access", "public"]),
    RegulationDefinition("PROV", "Provenance SLA", RegulationTier.MANDATORY, 0.95, ["catalog", "data"]),
    RegulationDefinition("INS", "Insurance Coverage", RegulationTier.MANDATORY, 0.8, ["finance", "ops"]),
    RegulationDefinition("CARBON", "Carbon Reporting", RegulationTier.RECOMMENDED, 0.5, ["sustainability"]),
    RegulationDefinition("DEI", "DEI Standards", RegulationTier.RECOMMENDED, 0.6, ["hr", "programming"]),
    RegulationDefinition("IP", "IP Clearance", RegulationTier.MANDATORY, 0.9, ["legal", "catalog"]),
]


def build_compliance_matrix(
    checks: list[ComplianceCheck],
    regulations: list[RegulationDefinition] | None = None,
) -> ComplianceMatrix:
    """Build a domain x regulation compliance matrix from check results."""
    regs = regulations or DEFAULT_REGULATIONS
    check_map = {c.regulation: c for c in checks}
    domains = sorted({d for r in regs for d in r.domains})
    cells: list[MatrixCell] = []

    for reg in regs:
        check = check_map.get(reg.code) or check_map.get(reg.name)
        passed = check.passed if check else False
        notes = check.notes if check else "not assessed"
        base_score = 1.0 if passed else 0.0
        for domain in reg.domains or ["general"]:
            cell_score = base_score * reg.weight
            cells.append(
                MatrixCell(
                    regulation=reg.code,
                    domain=domain,
                    passed=passed,
                    score=round(cell_score, 3),
                    notes=notes,
                )
            )

    domain_totals: dict[str, list[float]] = {d: [] for d in domains}
    for cell in cells:
        domain_totals.setdefault(cell.domain, []).append(cell.score)
    domain_scores = {
        d: round(sum(scores) / len(scores), 3) if scores else 0.0
        for d, scores in domain_totals.items()
    }

    weighted_sum = sum(c.score for c in cells)
    weight_total = sum(r.weight * max(1, len(r.domains)) for r in regs)
    overall = weighted_sum / weight_total if weight_total else 0.0

    gaps = [
        f"{c.regulation}/{c.domain}"
        for c in cells
        if not c.passed and any(r.code == c.regulation and r.tier == RegulationTier.MANDATORY for r in regs)
    ]

    return ComplianceMatrix(
        domains=domains,
        regulations=[r.code for r in regs],
        cells=cells,
        overall_score=round(overall, 3),
        domain_scores=domain_scores,
        gaps=gaps,
    )


def matrix_from_report(report: ComplianceReport) -> ComplianceMatrix:
    return build_compliance_matrix(report.checks)


def merge_matrices(matrices: Iterable[ComplianceMatrix]) -> ComplianceMatrix:
    """Merge multiple matrices by averaging cell scores."""
    mats = list(matrices)
    if not mats:
        return ComplianceMatrix([], [], [], 0.0)
    domains = sorted({d for m in mats for d in m.domains})
    regulations = sorted({r for m in mats for r in m.regulations})
    cell_scores: dict[tuple[str, str], list[float]] = {}
    cell_pass: dict[tuple[str, str], list[bool]] = {}
    for m in mats:
        for c in m.cells:
            key = (c.regulation, c.domain)
            cell_scores.setdefault(key, []).append(c.score)
            cell_pass.setdefault(key, []).append(c.passed)
    cells = [
        MatrixCell(
            regulation=reg,
            domain=dom,
            passed=all(cell_pass.get((reg, dom), [False])),
            score=round(sum(cell_scores.get((reg, dom), [0.0])) / len(mats), 3),
        )
        for reg in regulations
        for dom in domains
        if (reg, dom) in cell_scores
    ]
    overall = sum(m.overall_score for m in mats) / len(mats)
    domain_scores: dict[str, list[float]] = {}
    for m in mats:
        for d, s in m.domain_scores.items():
            domain_scores.setdefault(d, []).append(s)
    return ComplianceMatrix(
        domains=domains,
        regulations=regulations,
        cells=cells,
        overall_score=round(overall, 3),
        domain_scores={d: round(sum(v) / len(v), 3) for d, v in domain_scores.items()},
        gaps=sorted({g for m in mats for g in m.gaps}),
    )


def remediation_priority(matrix: ComplianceMatrix) -> list[tuple[str, float]]:
    """Rank gaps by severity (mandatory failures first)."""
    reg_tiers = {r.code: r for r in DEFAULT_REGULATIONS}
    priorities: list[tuple[str, float]] = []
    for gap in matrix.gaps:
        reg_code = gap.split("/")[0]
        reg = reg_tiers.get(reg_code)
        weight = reg.weight if reg else 0.5
        tier_boost = 2.0 if reg and reg.tier == RegulationTier.MANDATORY else 1.0
        priorities.append((gap, weight * tier_boost))
    return sorted(priorities, key=lambda x: -x[1])


def compliance_heatmap_rows(matrix: ComplianceMatrix) -> list[dict[str, object]]:
    """Serialize matrix as heatmap rows for dashboards."""
    rows: list[dict[str, object]] = []
    for domain in matrix.domains:
        row: dict[str, object] = {"domain": domain}
        for reg in matrix.regulations:
            cell = next((c for c in matrix.cells if c.regulation == reg and c.domain == domain), None)
            row[reg] = cell.score if cell else 0.0
        rows.append(row)
    return rows


def assess_readiness(matrix: ComplianceMatrix, threshold: float = 0.85) -> dict[str, object]:
    ready = matrix.overall_score >= threshold and not matrix.gaps
    return {
        "ready": ready,
        "score": matrix.overall_score,
        "threshold": threshold,
        "blocking_gaps": matrix.gaps,
        "weakest_domain": min(matrix.domain_scores, key=matrix.domain_scores.get) if matrix.domain_scores else None,
    }
