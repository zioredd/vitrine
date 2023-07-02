"""K-means-ish theme clustering for crowd analytics."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field

from vitrine_types.models import Artwork, Exhibition


@dataclass
class ClusterCentroid:
    label: str
    features: list[float]
    member_count: int = 0


@dataclass
class ThemeClusterResult:
    cluster_id: int
    label: str
    members: list[str]
    centroid: ClusterCentroid
    inertia_contribution: float
    dominant_tags: list[str] = field(default_factory=list)


@dataclass
class ClusteringReport:
    exhibition_id: str
    clusters: list[ThemeClusterResult]
    k: int
    total_inertia: float
    silhouette_estimate: float


def _artwork_features(artwork: Artwork) -> list[float]:
    tag_hash = sum(hash(t) % 100 for t in artwork.tags) / max(1, len(artwork.tags)) / 100.0
    return [
        artwork.intensity,
        artwork.narrative_tension,
        artwork.wall_text_ratio,
        min(1.0, artwork.dwell_sec / 300.0),
        tag_hash,
    ]


def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _mean_vectors(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]


def _assign_clusters(
    features: list[tuple[str, list[float]]],
    centroids: list[list[float]],
) -> list[int]:
    assignments: list[int] = []
    for _, feat in features:
        distances = [_euclidean(feat, c) for c in centroids]
        assignments.append(distances.index(min(distances)))
    return assignments


def kmeans_theme_clusters(
    exhibition: Exhibition,
    k: int = 3,
    max_iterations: int = 50,
    seed: int = 42,
) -> ClusteringReport:
    """K-means clustering on artwork feature vectors."""
    arts = exhibition.all_artworks()
    if not arts:
        return ClusteringReport(exhibition.id, [], 0, 0.0, 0.0)

    k = min(k, len(arts))
    rng = random.Random(seed)
    features = [(a.id, _artwork_features(a)) for a in arts]

    indices = rng.sample(range(len(features)), k)
    centroids = [list(features[i][1]) for i in indices]

    assignments = [0] * len(features)
    for _ in range(max_iterations):
        new_assignments = _assign_clusters(features, centroids)
        if new_assignments == assignments:
            break
        assignments = new_assignments
        for cluster_idx in range(k):
            members = [feat for (_, feat), a in zip(features, assignments) if a == cluster_idx]
            if members:
                centroids[cluster_idx] = _mean_vectors(members)

    clusters_map: dict[int, list[str]] = defaultdict(list)
    inertia_total = 0.0
    for (art_id, feat), cluster_idx in zip(features, assignments):
        clusters_map[cluster_idx].append(art_id)
        inertia_total += _euclidean(feat, centroids[cluster_idx]) ** 2

    art_by_id = {a.id: a for a in arts}
    results: list[ThemeClusterResult] = []
    for cluster_idx in range(k):
        member_ids = clusters_map.get(cluster_idx, [])
        if not member_ids:
            continue
        tag_counts: dict[str, int] = defaultdict(int)
        for mid in member_ids:
            for tag in art_by_id[mid].tags:
                tag_counts[tag] += 1
        dominant = sorted(tag_counts, key=lambda t: -tag_counts[t])[:3]
        label = dominant[0] if dominant else f"cluster-{cluster_idx}"

        member_feats = [feat for (aid, feat), a in zip(features, assignments) if a == cluster_idx and aid in member_ids]
        inertia = sum(_euclidean(f, centroids[cluster_idx]) ** 2 for f in member_feats)

        results.append(
            ThemeClusterResult(
                cluster_id=cluster_idx,
                label=label,
                members=member_ids,
                centroid=ClusterCentroid(label=label, features=centroids[cluster_idx], member_count=len(member_ids)),
                inertia_contribution=round(inertia, 4),
                dominant_tags=dominant,
            )
        )

    silhouette = _estimate_silhouette(features, assignments, centroids)
    return ClusteringReport(
        exhibition_id=exhibition.id,
        clusters=sorted(results, key=lambda c: -c.centroid.member_count),
        k=k,
        total_inertia=round(inertia_total, 4),
        silhouette_estimate=round(silhouette, 3),
    )


def _estimate_silhouette(
    features: list[tuple[str, list[float]]],
    assignments: list[int],
    centroids: list[list[float]],
) -> float:
    if len(features) < 2 or len(centroids) < 2:
        return 0.0
    scores: list[float] = []
    for (_, feat), cluster_idx in zip(features, assignments):
        a = _euclidean(feat, centroids[cluster_idx])
        other_dists = [_euclidean(feat, centroids[j]) for j in range(len(centroids)) if j != cluster_idx]
        b = min(other_dists) if other_dists else a
        if max(a, b) <= 0:
            scores.append(0.0)
        else:
            scores.append((b - a) / max(a, b))
    return sum(scores) / len(scores)


def find_optimal_k(
    exhibition: Exhibition,
    k_range: range | None = None,
    seed: int = 42,
) -> tuple[int, list[tuple[int, float]]]:
    """Elbow method: find k with diminishing inertia reduction."""
    arts = exhibition.all_artworks()
    if len(arts) < 2:
        return 1, [(1, 0.0)]

    max_k = min(len(arts), 8)
    k_range = k_range or range(2, max_k + 1)
    inertias: list[tuple[int, float]] = []
    for k in k_range:
        report = kmeans_theme_clusters(exhibition, k=k, seed=seed)
        inertias.append((k, report.total_inertia))

    best_k = k_range.start
    best_drop = 0.0
    for i in range(1, len(inertias)):
        drop = inertias[i - 1][1] - inertias[i][1]
        if drop > best_drop:
            best_drop = drop
            best_k = inertias[i][0]

    return best_k, inertias


def merge_small_clusters(
    report: ClusteringReport,
    min_size: int = 2,
) -> ClusteringReport:
    """Merge clusters below min_size into nearest neighbor."""
    large = [c for c in report.clusters if len(c.members) >= min_size]
    small = [c for c in report.clusters if len(c.members) < min_size]
    if not small or not large:
        return report

    for sc in small:
        nearest = min(
            large,
            key=lambda lc: _euclidean(sc.centroid.features, lc.centroid.features),
        )
        nearest.members.extend(sc.members)
        nearest.centroid.member_count = len(nearest.members)

    return ClusteringReport(
        exhibition_id=report.exhibition_id,
        clusters=large,
        k=len(large),
        total_inertia=report.total_inertia,
        silhouette_estimate=report.silhouette_estimate,
    )
