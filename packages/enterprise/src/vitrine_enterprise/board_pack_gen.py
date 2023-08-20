"""Expanded board pack generators with sections and appendices."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from vitrine_core.intelligence import build_intelligence_report
from vitrine_enterprise.compliance_matrix import ComplianceMatrix, matrix_from_report
from vitrine_enterprise.forecasting import BudgetForecast, forecast_budget_office
from vitrine_enterprise.incidents import IncidentPortfolio, score_portfolio
from vitrine_enterprise.program import (
    BoardPack,
    BudgetOffice,
    ComplianceReport,
    ExecutiveProgram,
    IncidentResponse,
    build_board_pack,
)
from vitrine_types.models import Exhibition


@dataclass
class BoardSection:
    title: str
    summary: str
    metrics: dict[str, float]
    bullets: list[str] = field(default_factory=list)


@dataclass
class BoardAppendix:
    name: str
    content_type: str
    data: dict[str, Any]


@dataclass
class ExpandedBoardPack:
    period: str
    generated_on: date
    executive_summary: str
    sections: list[BoardSection]
    appendices: list[BoardAppendix]
    base_pack: BoardPack
    forecast: BudgetForecast | None = None
    compliance_matrix: ComplianceMatrix | None = None
    incident_portfolio: IncidentPortfolio | None = None
    risk_flags: list[str] = field(default_factory=list)


def _program_section(programs: list[ExecutiveProgram]) -> BoardSection:
    total_budget = sum(p.budget_allocated for p in programs)
    total_spent = sum(p.budget_spent for p in programs)
    util = total_spent / total_budget if total_budget else 0.0
    bullets = [
        f"{p.name}: {len(p.exhibitions)} exhibitions, {p.utilization:.0%} budget used"
        for p in programs[:5]
    ]
    return BoardSection(
        title="Executive Programs",
        summary=f"{len(programs)} active programs with {util:.0%} aggregate utilization.",
        metrics={
            "program_count": float(len(programs)),
            "budget_utilization": round(util, 3),
            "total_allocated": total_budget,
            "total_spent": total_spent,
        },
        bullets=bullets,
    )


def _catalog_section(exhibitions: list[Exhibition]) -> BoardSection:
    intel = build_intelligence_report(exhibitions, alerts=[])
    genres = len({e.genre for e in exhibitions if e.genre})
    residencies = len({e.residency for e in exhibitions if e.residency})
    return BoardSection(
        title="Catalog Health",
        summary=(
            f"{intel.exhibition_count} exhibitions; average Vitrine score "
            f"{intel.avg_vitrine_score:.1f}; stress index {intel.catalog_stress_index:.2f}."
        ),
        metrics={
            "exhibition_count": float(intel.exhibition_count),
            "avg_vitrine_score": intel.avg_vitrine_score,
            "catalog_stress": intel.catalog_stress_index,
            "genre_diversity": float(genres),
            "residency_count": float(residencies),
        },
        bullets=[
            f"Top genre diversity: {genres} genres represented",
            f"Residency programs: {residencies}",
        ],
    )


def _financial_section(forecast: BudgetForecast | None, office: BudgetOffice | None) -> BoardSection:
    if forecast:
        return BoardSection(
            title="Financial Outlook",
            summary=forecast.narrative,
            metrics={
                "total_projected": forecast.total_projected,
                "total_planned": forecast.total_planned,
                "risk_category_count": float(len(forecast.risk_categories)),
            },
            bullets=[f"At-risk: {cat}" for cat in forecast.risk_categories[:5]],
        )
    if office:
        return BoardSection(
            title="Financial Outlook",
            summary=f"FY{office.fiscal_year} variance ${office.total_variance():,.0f}.",
            metrics={"total_variance": office.total_variance()},
            bullets=office.overspend_categories(),
        )
    return BoardSection(title="Financial Outlook", summary="No financial data.", metrics={})


def _governance_section(
    matrix: ComplianceMatrix | None,
    incidents: IncidentPortfolio | None,
) -> BoardSection:
    bullets: list[str] = []
    metrics: dict[str, float] = {}
    if matrix:
        metrics["compliance_score"] = matrix.overall_score
        bullets.extend(f"Gap: {g}" for g in matrix.gaps[:3])
    if incidents:
        metrics["incident_risk"] = incidents.aggregate_risk
        metrics["open_critical"] = float(incidents.open_critical)
        bullets.extend(incidents.recommendations[:3])
    summary_parts = []
    if matrix:
        summary_parts.append(f"compliance {matrix.overall_score:.0%}")
    if incidents:
        summary_parts.append(f"incident risk {incidents.aggregate_risk:.2f}")
    return BoardSection(
        title="Governance & Risk",
        summary="; ".join(summary_parts) or "Governance metrics pending.",
        metrics=metrics,
        bullets=bullets,
    )


def generate_expanded_board_pack(
    exhibitions: list[Exhibition],
    programs: list[ExecutiveProgram],
    compliance: ComplianceReport,
    incidents: IncidentResponse,
    *,
    budget_office: BudgetOffice | None = None,
    period: str = "Q2 2026",
    generated_on: date | None = None,
) -> ExpandedBoardPack:
    """Generate a full board pack with sections, forecast, and appendices."""
    generated_on = generated_on or date.today()
    base = build_board_pack(exhibitions, programs, compliance, incidents, period=period)

    forecast = forecast_budget_office(budget_office) if budget_office else None
    matrix = matrix_from_report(compliance)
    incident_pf = score_portfolio(incidents)

    sections = [
        _catalog_section(exhibitions),
        _program_section(programs),
        _financial_section(forecast, budget_office),
        _governance_section(matrix, incident_pf),
    ]

    appendices: list[BoardAppendix] = [
        BoardAppendix(
            name="KPI Detail",
            content_type="metrics",
            data=base.kpis,
        ),
        BoardAppendix(
            name="Program Roster",
            content_type="table",
            data={"programs": [{"name": p.name, "exhibitions": len(p.exhibitions)} for p in programs]},
        ),
    ]
    if matrix:
        appendices.append(
            BoardAppendix(name="Compliance Matrix", content_type="matrix", data={"score": matrix.overall_score, "gaps": matrix.gaps})
        )

    risk_flags: list[str] = []
    if matrix and matrix.gaps:
        risk_flags.append("compliance_gaps")
    if incident_pf.open_critical > 0:
        risk_flags.append("critical_incidents")
    if forecast and forecast.risk_categories:
        risk_flags.append("budget_overspend")

    exec_summary = (
        f"{base.executive_summary} "
        f"Board pack generated {generated_on.isoformat()} with {len(sections)} sections."
    )

    return ExpandedBoardPack(
        period=period,
        generated_on=generated_on,
        executive_summary=exec_summary,
        sections=sections,
        appendices=appendices,
        base_pack=base,
        forecast=forecast,
        compliance_matrix=matrix,
        incident_portfolio=incident_pf,
        risk_flags=risk_flags,
    )


def board_pack_to_dict(pack: ExpandedBoardPack) -> dict[str, Any]:
    """Serialize expanded board pack for API responses."""
    return {
        "period": pack.period,
        "generated_on": pack.generated_on.isoformat(),
        "executive_summary": pack.executive_summary,
        "risk_flags": pack.risk_flags,
        "sections": [
            {
                "title": s.title,
                "summary": s.summary,
                "metrics": s.metrics,
                "bullets": s.bullets,
            }
            for s in pack.sections
        ],
        "appendices": [{"name": a.name, "type": a.content_type, "data": a.data} for a in pack.appendices],
        "kpis": pack.base_pack.kpis,
    }


def executive_brief(pack: ExpandedBoardPack, max_bullets: int = 5) -> str:
    """One-paragraph executive brief from expanded pack."""
    bullets: list[str] = []
    for section in pack.sections:
        bullets.extend(section.bullets)
    top = bullets[:max_bullets]
    bullet_text = "; ".join(top) if top else "No action items."
    return f"{pack.executive_summary} Key items: {bullet_text}"
