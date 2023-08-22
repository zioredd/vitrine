"""Budget forecasting with linear trend lines and variance projection."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Sequence

from vitrine_enterprise.program import BudgetLine, BudgetOffice


@dataclass
class TrendPoint:
    period_index: int
    label: str
    planned: float
    actual: float
    projected: float | None = None


@dataclass
class TrendLine:
    slope: float
    intercept: float
    r_squared: float

    def predict(self, x: float) -> float:
        return self.slope * x + self.intercept


@dataclass
class CategoryForecast:
    category: str
    current_actual: float
    current_planned: float
    trend: TrendLine
    projected_next: float
    confidence: float
    variance_trend: float


@dataclass
class BudgetForecast:
    fiscal_year: int
    as_of: date
    categories: list[CategoryForecast]
    total_projected: float
    total_planned: float
    risk_categories: list[str] = field(default_factory=list)
    narrative: str = ""


def _linear_regression(xs: Sequence[float], ys: Sequence[float]) -> TrendLine:
    n = len(xs)
    if n < 2:
        y = ys[0] if ys else 0.0
        return TrendLine(slope=0.0, intercept=y, r_squared=1.0)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope = num / den if den else 0.0
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot else 1.0
    return TrendLine(slope=slope, intercept=intercept, r_squared=max(0.0, min(1.0, r2)))


def build_trend_points(
    history: list[tuple[str, float, float]],
) -> list[TrendPoint]:
    """Build trend points from (label, planned, actual) tuples."""
    points: list[TrendPoint] = []
    for i, (label, planned, actual) in enumerate(history):
        points.append(TrendPoint(period_index=i, label=label, planned=planned, actual=actual))
    return points


def forecast_category(
    category: str,
    history: list[tuple[str, float, float]],
    horizon_index: int | None = None,
) -> CategoryForecast:
    """Forecast a single budget category from historical periods."""
    if not history:
        return CategoryForecast(
            category=category,
            current_actual=0.0,
            current_planned=0.0,
            trend=TrendLine(0.0, 0.0, 0.0),
            projected_next=0.0,
            confidence=0.0,
            variance_trend=0.0,
        )

    xs = [float(i) for i in range(len(history))]
    actuals = [h[2] for h in history]
    planned = [h[1] for h in history]
    trend = _linear_regression(xs, actuals)
    next_x = horizon_index if horizon_index is not None else len(history)
    projected = max(0.0, trend.predict(next_x))

    variances = [a - p for (_, p, a) in history]
    var_trend = _linear_regression(xs, variances).slope if len(variances) >= 2 else variances[-1]

    confidence = trend.r_squared * min(1.0, len(history) / 6.0)

    return CategoryForecast(
        category=category,
        current_actual=actuals[-1],
        current_planned=planned[-1],
        trend=trend,
        projected_next=round(projected, 2),
        confidence=round(confidence, 3),
        variance_trend=round(var_trend, 2),
    )


def forecast_budget_office(
    office: BudgetOffice,
    category_history: dict[str, list[tuple[str, float, float]]] | None = None,
    as_of: date | None = None,
    overspend_threshold: float = 0.05,
) -> BudgetForecast:
    """Produce multi-category forecast from current office state and optional history."""
    as_of = as_of or date.today()
    forecasts: list[CategoryForecast] = []

    for line in office.lines:
        history = (category_history or {}).get(line.category)
        if history:
            fc = forecast_category(line.category, history)
        else:
            synthetic = [
                ("Q1", line.planned * 0.25, line.actual * 0.22),
                ("Q2", line.planned * 0.5, line.actual * 0.48),
                ("Q3", line.planned * 0.75, line.actual * 0.72),
                ("Q4", line.planned, line.actual),
            ]
            fc = forecast_category(line.category, synthetic)
        forecasts.append(fc)

    total_projected = sum(f.projected_next for f in forecasts)
    total_planned = sum(line.planned for line in office.lines)
    risk = [
        f.category
        for f in forecasts
        if f.projected_next > next(l.planned for l in office.lines if l.category == f.category)
        * (1.0 + overspend_threshold)
    ]

    overspend_total = total_projected - total_planned
    direction = "over" if overspend_total > 0 else "under"
    narrative = (
        f"FY{office.fiscal_year} forecast as of {as_of.isoformat()}: "
        f"projected spend ${total_projected:,.0f} vs planned ${total_planned:,.0f} "
        f"({direction} by ${abs(overspend_total):,.0f}). "
        f"{len(risk)} categories flagged for overspend risk."
    )

    return BudgetForecast(
        fiscal_year=office.fiscal_year,
        as_of=as_of,
        categories=forecasts,
        total_projected=round(total_projected, 2),
        total_planned=round(total_planned, 2),
        risk_categories=risk,
        narrative=narrative,
    )


def rolling_forecast(
    lines: list[BudgetLine],
    periods: list[str],
    actuals_by_period: dict[str, dict[str, float]],
) -> list[BudgetForecast]:
    """Generate rolling forecasts for each period using expanding window."""
    results: list[BudgetForecast] = []
    for end_idx in range(2, len(periods) + 1):
        window = periods[:end_idx]
        history_map: dict[str, list[tuple[str, float, float]]] = {}
        for line in lines:
            hist: list[tuple[str, float, float]] = []
            for i, period in enumerate(window):
                frac = (i + 1) / len(periods)
                planned = line.planned * frac
                actual = actuals_by_period.get(period, {}).get(line.category, planned * 0.95)
                hist.append((period, planned, actual))
            history_map[line.category] = hist
        office = BudgetOffice(fiscal_year=2026, lines=lines)
        results.append(forecast_budget_office(office, category_history=history_map))
    return results


def confidence_band(forecast: CategoryForecast, sigma: float = 0.15) -> tuple[float, float]:
    """Return lower/upper bounds using R²-adjusted sigma."""
    spread = forecast.projected_next * sigma * (1.0 - forecast.confidence)
    return (
        round(max(0.0, forecast.projected_next - spread), 2),
        round(forecast.projected_next + spread, 2),
    )


def aggregate_forecast_metrics(forecasts: list[CategoryForecast]) -> dict[str, float]:
    if not forecasts:
        return {"avg_confidence": 0.0, "avg_slope": 0.0, "categories_at_risk": 0.0}
    return {
        "avg_confidence": round(sum(f.confidence for f in forecasts) / len(forecasts), 3),
        "avg_slope": round(sum(f.trend.slope for f in forecasts) / len(forecasts), 3),
        "categories_at_risk": float(sum(1 for f in forecasts if f.variance_trend > 0)),
    }


def extrapolate_year_end(
    office: BudgetOffice,
    months_elapsed: int,
    months_total: int = 12,
) -> float:
    """Simple run-rate extrapolation to fiscal year end."""
    if months_elapsed <= 0:
        return office.total_variance()
    spent = sum(line.actual for line in office.lines)
    run_rate = spent / months_elapsed
    projected = run_rate * months_total
    planned = sum(line.planned for line in office.lines)
    return round(projected - planned, 2)
