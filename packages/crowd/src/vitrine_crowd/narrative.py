"""Crowd narrative analytics: relationship web, arc, theme clusters."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from vitrine_graph.graph import build_exhibition_graph
from vitrine_types.models import Exhibition, GraphEdge, GraphNode


@dataclass
class WebNode:
    id: str
    label: str
    degree: int


@dataclass
class WebEdge:
    source: str
    target: str
    weight: float


@dataclass
class RelationshipWeb:
    nodes: list[WebNode]
    edges: list[WebEdge]
    density: float


@dataclass
class ArcReport:
    completeness: float
    tension_span: float
    narrative_gaps: int


@dataclass
class ThemeCluster:
    label: str
    members: list[str]
    weight: float


@dataclass
class ResidencyLens:
    residency: str
    exhibition_count: int
    avg_crowd_score: float
    series_breakdown: dict[str, int] = field(default_factory=dict)


def relationship_web(exhibition: Exhibition) -> RelationshipWeb:
    """Build artwork relationship web from graph or tag co-occurrence."""
    if exhibition.graph_nodes:
        graph = build_exhibition_graph(exhibition)
        degree: Counter[str] = Counter()
        edges: list[WebEdge] = []
        for src, neighbors in graph.adjacency.items():
            for tgt, w in neighbors:
                degree[src] += 1
                degree[tgt] += 1
                edges.append(WebEdge(source=src, target=tgt, weight=w))
        nodes = [
            WebNode(id=nid, label=graph.nodes[nid].label, degree=degree[nid])
            for nid in graph.nodes
        ]
    else:
        # Fallback: tag co-occurrence among artworks
        arts = exhibition.all_artworks()
        tag_map: dict[str, set[str]] = defaultdict(set)
        for art in arts:
            for tag in art.tags:
                tag_map[tag].add(art.id)
        edges = []
        seen: set[tuple[str, str]] = set()
        for members in tag_map.values():
            ids = sorted(members)
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pair = (ids[i], ids[j])
                    if pair not in seen:
                        seen.add(pair)
                        edges.append(WebEdge(source=pair[0], target=pair[1], weight=1.0))
        degree = Counter()
        for e in edges:
            degree[e.source] += 1
            degree[e.target] += 1
        nodes = [WebNode(id=a.id, label=a.title, degree=degree[a.id]) for a in arts]
    n = len(nodes)
    max_edges = n * (n - 1) / 2 if n > 1 else 1
    density = len(edges) / max_edges if max_edges else 0.0
    return RelationshipWeb(nodes=nodes, edges=edges, density=round(density, 3))


def arc_completeness(exhibition: Exhibition) -> ArcReport:
    """Measure narrative arc via tension curve across artworks."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    if len(arts) < 2:
        return ArcReport(completeness=0.0, tension_span=0.0, narrative_gaps=0)
    tensions = [a.narrative_tension for a in arts]
    span = max(tensions) - min(tensions)
    gaps = sum(1 for i in range(len(tensions) - 1) if abs(tensions[i + 1] - tensions[i]) > 0.5)
    # Completeness: has rise and resolution pattern
    mid = len(tensions) // 2
    first_half_avg = sum(tensions[:mid]) / max(1, mid)
    second_half_avg = sum(tensions[mid:]) / max(1, len(tensions) - mid)
    has_arc = span >= 0.3 and abs(first_half_avg - second_half_avg) >= 0.05
    completeness = min(1.0, span + (0.3 if has_arc else 0.0))
    return ArcReport(
        completeness=round(completeness, 3),
        tension_span=round(span, 3),
        narrative_gaps=gaps,
    )


def theme_clusters(exhibition: Exhibition, min_size: int = 2) -> list[ThemeCluster]:
    """Cluster artworks by shared tags."""
    tag_to_arts: dict[str, list[str]] = defaultdict(list)
    for art in exhibition.all_artworks():
        for tag in art.tags:
            tag_to_arts[tag].append(art.id)
    clusters: list[ThemeCluster] = []
    for tag, members in sorted(tag_to_arts.items()):
        if len(members) >= min_size:
            weight = len(members) / max(1, len(exhibition.all_artworks()))
            clusters.append(ThemeCluster(label=tag, members=members, weight=round(weight, 3)))
    return clusters


def residency_lens(exhibitions: list[Exhibition], residency: str) -> ResidencyLens:
    """Aggregate crowd metrics for a residency program."""
    matching = [e for e in exhibitions if e.residency == residency]
    scores = [e.crowd_score for e in matching if e.crowd_score is not None]
    avg = sum(scores) / len(scores) if scores else 0.0
    series: Counter[str] = Counter()
    for e in matching:
        series[e.series or "ungrouped"] += 1
    return ResidencyLens(
        residency=residency,
        exhibition_count=len(matching),
        avg_crowd_score=round(avg, 2),
        series_breakdown=dict(series),
    )
