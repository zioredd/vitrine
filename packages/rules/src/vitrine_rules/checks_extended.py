"""Extended data-quality checks: venue, dates, tags, graph, signal freshness."""

from __future__ import annotations

import math
from collections import Counter, deque
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from vitrine_graph.graph import build_exhibition_graph
from vitrine_types.models import Exhibition, Severity, Signal, Tag

from vitrine_rules.models import RuleViolation


def _venue_key(exhibition: Exhibition) -> str | None:
    if exhibition.venue is None:
        return None
    parts = [
        exhibition.venue.name.strip().lower(),
        (exhibition.venue.city or "").strip().lower(),
        (exhibition.venue.country or "").strip().lower(),
    ]
    return "|".join(parts)


def check_venue_consistency(
    exhibition: Exhibition,
    *,
    require_venue: bool = True,
    format_must_match_genre: bool = False,
) -> list[RuleViolation]:
    """Ensure venue metadata is present and internally consistent."""
    violations: list[RuleViolation] = []
    venue = exhibition.venue

    if venue is None:
        if require_venue:
            violations.append(
                RuleViolation(
                    rule="venue_consistency",
                    message="exhibition missing venue metadata",
                    severity=Severity.WARN,
                    exhibition_id=exhibition.id,
                )
            )
        return violations

    if not venue.name or len(venue.name.strip()) < 2:
        violations.append(
            RuleViolation(
                rule="venue_consistency",
                message="venue name too short or missing",
                severity=Severity.ERROR,
                exhibition_id=exhibition.id,
            )
        )

    if venue.city and venue.country and venue.city.lower() == venue.country.lower():
        violations.append(
            RuleViolation(
                rule="venue_consistency",
                message="venue city and country appear identical",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    if venue.capacity is not None and venue.capacity < 10:
        violations.append(
            RuleViolation(
                rule="venue_consistency",
                message=f"venue capacity {venue.capacity} unusually low",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )

    if format_must_match_genre and venue.format and exhibition.genre:
        fmt = venue.format.lower()
        genre = exhibition.genre.lower()
        if fmt not in genre and genre not in fmt:
            violations.append(
                RuleViolation(
                    rule="venue_consistency",
                    message=f"venue format '{venue.format}' diverges from genre '{exhibition.genre}'",
                    severity=Severity.INFO,
                    exhibition_id=exhibition.id,
                )
            )

    return violations


def check_date_range(
    exhibition: Exhibition,
    *,
    max_duration_days: int = 730,
    min_duration_days: int = 1,
    allow_future_open: bool = True,
) -> list[RuleViolation]:
    """Validate exhibition open/close dates and duration bounds."""
    violations: list[RuleViolation] = []
    opened = exhibition.opened_on
    closed = exhibition.closed_on

    if opened is None and closed is None:
        violations.append(
            RuleViolation(
                rule="date_range",
                message="no exhibition dates defined",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )
        return violations

    if opened is not None and closed is not None:
        if closed < opened:
            violations.append(
                RuleViolation(
                    rule="date_range",
                    message=f"closed_on {closed} precedes opened_on {opened}",
                    severity=Severity.ERROR,
                    exhibition_id=exhibition.id,
                )
            )
            return violations

        duration = (closed - opened).days
        if duration < min_duration_days:
            violations.append(
                RuleViolation(
                    rule="date_range",
                    message=f"duration {duration}d below minimum {min_duration_days}d",
                    severity=Severity.WARN,
                    exhibition_id=exhibition.id,
                )
            )
        if duration > max_duration_days:
            violations.append(
                RuleViolation(
                    rule="date_range",
                    message=f"duration {duration}d exceeds maximum {max_duration_days}d",
                    severity=Severity.WARN,
                    exhibition_id=exhibition.id,
                )
            )

    today = date.today()
    if not allow_future_open and opened and opened > today:
        violations.append(
            RuleViolation(
                rule="date_range",
                message=f"opened_on {opened} is in the future",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    if closed and closed < today - timedelta(days=365 * 10):
        violations.append(
            RuleViolation(
                rule="date_range",
                message=f"closed_on {closed} more than 10 years ago",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    return violations


def _tag_density_score(tags: list[Tag], artwork_count: int) -> float:
    if artwork_count <= 0:
        return 0.0
    weighted = sum(t.weight for t in tags)
    return weighted / artwork_count


def check_tag_density(
    exhibition: Exhibition,
    *,
    min_density: float = 0.15,
    max_density: float = 8.0,
    min_unique_tags: int = 1,
) -> list[RuleViolation]:
    """Flag exhibitions with too few or too many tags relative to artwork count."""
    violations: list[RuleViolation] = []
    arts = exhibition.all_artworks()
    art_count = len(arts)
    tag_count = len(exhibition.tags)
    density = _tag_density_score(exhibition.tags, max(1, art_count))

    if tag_count < min_unique_tags:
        violations.append(
            RuleViolation(
                rule="tag_density",
                message=f"only {tag_count} exhibition tags (min {min_unique_tags})",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )

    if density < min_density and art_count >= 3:
        violations.append(
            RuleViolation(
                rule="tag_density",
                message=f"tag density {density:.2f} below minimum {min_density}",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    if density > max_density:
        violations.append(
            RuleViolation(
                rule="tag_density",
                message=f"tag density {density:.2f} exceeds maximum {max_density}",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )

    art_tag_counts = Counter()
    for art in arts:
        for tag in art.tags:
            art_tag_counts[tag] += 1
    orphan_tags = [t.label for t in exhibition.tags if t.label not in art_tag_counts]
    if orphan_tags and len(orphan_tags) > tag_count * 0.5:
        violations.append(
            RuleViolation(
                rule="tag_density",
                message=f"{len(orphan_tags)} exhibition tags not reflected on artworks",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    return violations


def _connected_components(adjacency: dict[str, list[tuple[str, float]]]) -> list[set[str]]:
    seen: set[str] = set()
    components: list[set[str]] = []
    undirected: dict[str, set[str]] = {n: set() for n in adjacency}
    for src, neighbors in adjacency.items():
        for tgt, _ in neighbors:
            undirected.setdefault(src, set()).add(tgt)
            undirected.setdefault(tgt, set()).add(src)

    for node in undirected:
        if node in seen:
            continue
        component: set[str] = set()
        queue: deque[str] = deque([node])
        while queue:
            cur = queue.popleft()
            if cur in seen:
                continue
            seen.add(cur)
            component.add(cur)
            for neighbor in undirected.get(cur, ()):
                if neighbor not in seen:
                    queue.append(neighbor)
        components.append(component)
    return components


def check_graph_connectivity(
    exhibition: Exhibition,
    *,
    require_single_component: bool = True,
    min_nodes: int = 2,
    max_isolated_ratio: float = 0.25,
) -> list[RuleViolation]:
    """Verify exhibition graph structure and connectivity."""
    violations: list[RuleViolation] = []
    nodes = exhibition.graph_nodes
    edges = exhibition.graph_edges

    if not nodes and not edges:
        arts = exhibition.all_artworks()
        if len(arts) >= min_nodes:
            violations.append(
                RuleViolation(
                    rule="graph_connectivity",
                    message="artworks present but no graph defined",
                    severity=Severity.INFO,
                    exhibition_id=exhibition.id,
                )
            )
        return violations

    graph = build_exhibition_graph(exhibition)
    node_ids = set(graph.nodes)
    edge_refs = set()
    for edge in edges:
        edge_refs.add(edge.source_id)
        edge_refs.add(edge.target_id)

    dangling = edge_refs - node_ids
    if dangling:
        violations.append(
            RuleViolation(
                rule="graph_connectivity",
                message=f"edges reference unknown nodes: {sorted(dangling)[:5]}",
                severity=Severity.ERROR,
                exhibition_id=exhibition.id,
            )
        )

    if len(graph.nodes) < min_nodes:
        violations.append(
            RuleViolation(
                rule="graph_connectivity",
                message=f"graph has {len(graph.nodes)} nodes (min {min_nodes})",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )

    components = _connected_components(graph.adjacency)
    if require_single_component and len(components) > 1:
        sizes = sorted((len(c) for c in components), reverse=True)
        violations.append(
            RuleViolation(
                rule="graph_connectivity",
                message=f"graph has {len(components)} disconnected components (sizes {sizes[:4]})",
                severity=Severity.WARN,
                exhibition_id=exhibition.id,
            )
        )

    if graph.adjacency:
        degrees = [len(neighbors) for neighbors in graph.adjacency.values()]
        isolated = sum(1 for d in degrees if d == 0)
        ratio = isolated / len(degrees)
        if ratio > max_isolated_ratio:
            violations.append(
                RuleViolation(
                    rule="graph_connectivity",
                    message=f"{isolated} isolated nodes ({ratio:.0%} of graph)",
                    severity=Severity.INFO,
                    exhibition_id=exhibition.id,
                )
            )

    return violations


def _signal_age_days(signal: Signal, reference: datetime | None = None) -> float | None:
    captured = signal.provenance.captured_at
    if captured is None:
        return None
    ref = reference or datetime.now(timezone.utc)
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=timezone.utc)
    delta = ref - captured
    return max(0.0, delta.total_seconds() / 86400.0)


def check_signal_freshness(
    exhibition: Exhibition,
    *,
    max_age_days: float = 365.0,
    stale_fraction_threshold: float = 0.5,
    require_captured_at: bool = False,
) -> list[RuleViolation]:
    """Detect stale or undated signals in exhibition provenance."""
    violations: list[RuleViolation] = []
    signals = exhibition.signals
    if not signals:
        return violations

    now = datetime.now(timezone.utc)
    ages: list[float] = []
    missing_ts = 0

    for sig in signals:
        age = _signal_age_days(sig, now)
        if age is None:
            missing_ts += 1
            if require_captured_at:
                violations.append(
                    RuleViolation(
                        rule="signal_freshness",
                        message=f"signal {sig.id} missing captured_at timestamp",
                        severity=Severity.WARN,
                        exhibition_id=exhibition.id,
                    )
                )
            continue
        ages.append(age)
        if age > max_age_days:
            violations.append(
                RuleViolation(
                    rule="signal_freshness",
                    message=f"signal {sig.id} age {age:.0f}d exceeds {max_age_days:.0f}d",
                    severity=Severity.WARN,
                    exhibition_id=exhibition.id,
                )
            )

    if ages:
        stale = sum(1 for a in ages if a > max_age_days)
        fraction = stale / len(signals)
        if fraction >= stale_fraction_threshold:
            violations.append(
                RuleViolation(
                    rule="signal_freshness",
                    message=f"{stale}/{len(signals)} signals stale ({fraction:.0%})",
                    severity=Severity.ERROR,
                    exhibition_id=exhibition.id,
                )
            )
        avg_age = sum(ages) / len(ages)
        if avg_age > max_age_days * 0.75:
            violations.append(
                RuleViolation(
                    rule="signal_freshness",
                    message=f"average signal age {avg_age:.0f}d trending stale",
                    severity=Severity.INFO,
                    exhibition_id=exhibition.id,
                )
            )

    if missing_ts > len(signals) * 0.5:
        violations.append(
            RuleViolation(
                rule="signal_freshness",
                message=f"{missing_ts}/{len(signals)} signals lack timestamps",
                severity=Severity.INFO,
                exhibition_id=exhibition.id,
            )
        )

    return violations


def run_extended_checks(
    exhibitions: Iterable[Exhibition],
) -> list[RuleViolation]:
    """Run all extended checks across exhibitions."""
    checks = [
        check_venue_consistency,
        check_date_range,
        check_tag_density,
        check_graph_connectivity,
        check_signal_freshness,
    ]
    violations: list[RuleViolation] = []
    for ex in exhibitions:
        for check in checks:
            violations.extend(check(ex))
    return violations
