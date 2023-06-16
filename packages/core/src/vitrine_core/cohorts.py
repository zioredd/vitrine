"""Audience cohort clustering via k-means-style iterative assignment."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from vitrine_types.models import Exhibition


@dataclass
class CohortCluster:
    cluster_id: int
    centroid_score: float
    centroid_intensity: float
    members: list[str] = field(default_factory=list)
    label: str = ""

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass
class ClusteringResult:
    clusters: list[CohortCluster]
    iterations: int
    inertia: float


def _feature_vector(ex: Exhibition) -> tuple[float, float]:
    score = ex.vitrine_score or ex.crowd_score or 50.0
    arts = ex.all_artworks()
    intensity = sum(a.intensity for a in arts) / len(arts) if arts else 0.5
    return score, intensity


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _init_centroids(
    vectors: list[tuple[float, float]],
    k: int,
    rng: random.Random,
) -> list[tuple[float, float]]:
    if len(vectors) <= k:
        return list(vectors)
    return rng.sample(vectors, k)


def cluster_audience_cohorts(
    exhibitions: list[Exhibition],
    k: int = 4,
    max_iterations: int = 50,
    seed: int = 42,
) -> ClusteringResult:
    """Partition exhibitions into k cohort clusters on score + intensity plane."""
    if not exhibitions:
        return ClusteringResult(clusters=[], iterations=0, inertia=0.0)

    k = min(k, len(exhibitions))
    rng = random.Random(seed)
    ids = [ex.id for ex in exhibitions]
    vectors = [_feature_vector(ex) for ex in exhibitions]

    centroids = _init_centroids(vectors, k, rng)
    assignments = [-1] * len(vectors)

    for iteration in range(max_iterations):
        changed = False
        for i, vec in enumerate(vectors):
            dists = [_distance(vec, c) for c in centroids]
            nearest = dists.index(min(dists))
            if assignments[i] != nearest:
                assignments[i] = nearest
                changed = True

        new_centroids: list[tuple[float, float]] = []
        for cluster_idx in range(k):
            members = [vectors[i] for i, a in enumerate(assignments) if a == cluster_idx]
            if members:
                avg_score = sum(m[0] for m in members) / len(members)
                avg_int = sum(m[1] for m in members) / len(members)
                new_centroids.append((avg_score, avg_int))
            else:
                new_centroids.append(centroids[cluster_idx])

        if not changed:
            break
        centroids = new_centroids
    else:
        iteration += 1

    clusters: list[CohortCluster] = []
    inertia = 0.0
    for cluster_idx in range(k):
        member_ids = [ids[i] for i, a in enumerate(assignments) if a == cluster_idx]
        centroid = centroids[cluster_idx]
        for i, a in enumerate(assignments):
            if a == cluster_idx:
                inertia += _distance(vectors[i], centroid) ** 2
        label = _label_cluster(centroid)
        clusters.append(
            CohortCluster(
                cluster_id=cluster_idx,
                centroid_score=round(centroid[0], 2),
                centroid_intensity=round(centroid[1], 3),
                members=member_ids,
                label=label,
            )
        )

    return ClusteringResult(
        clusters=sorted(clusters, key=lambda c: -c.centroid_score),
        iterations=iteration + 1,
        inertia=round(inertia, 3),
    )


def _label_cluster(centroid: tuple[float, float]) -> str:
    score, intensity = centroid
    if score >= 75 and intensity >= 0.6:
        return "high-impact dynamic"
    if score >= 75:
        return "critical acclaim"
    if intensity >= 0.6:
        return "visceral engagement"
    if score < 45:
        return "emerging attention"
    return "balanced mid-tier"


def cohort_migration_matrix(
    before: ClusteringResult,
    after: ClusteringResult,
    exhibition_ids: list[str],
) -> dict[str, dict[str, int]]:
    """Track how exhibitions move between cohort clusters across two snapshots."""
    before_map = {}
    for cluster in before.clusters:
        for ex_id in cluster.members:
            before_map[ex_id] = cluster.label

    after_map = {}
    for cluster in after.clusters:
        for ex_id in cluster.members:
            after_map[ex_id] = cluster.label

    matrix: dict[str, dict[str, int]] = {}
    for ex_id in exhibition_ids:
        src = before_map.get(ex_id, "unknown")
        dst = after_map.get(ex_id, "unknown")
        matrix.setdefault(src, {})
        matrix[src][dst] = matrix[src].get(dst, 0) + 1
    return matrix
