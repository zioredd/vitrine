"""Expanded similarity metrics: cosine feature vectors, Jaccard tags."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from vitrine_types.models import Artwork, Exhibition, Tag


@dataclass
class FeatureVector:
    dimensions: list[str]
    values: list[float]

    def magnitude(self) -> float:
        return math.sqrt(sum(v * v for v in self.values))

    def normalize(self) -> FeatureVector:
        mag = self.magnitude()
        if mag <= 0:
            return self
        return FeatureVector(self.dimensions, [v / mag for v in self.values])


@dataclass
class SimilarityResult:
    score: float
    cosine_similarity: float
    jaccard_tags: float
    genre_match: float
    score_proximity: float
    method: str = "composite"


def cosine_similarity(a: FeatureVector, b: FeatureVector) -> float:
    """Cosine similarity on aligned feature vectors."""
    dim_map_a = dict(zip(a.dimensions, a.values))
    dim_map_b = dict(zip(b.dimensions, b.values))
    all_dims = sorted(set(dim_map_a) | set(dim_map_b))
    va = [dim_map_a.get(d, 0.0) for d in all_dims]
    vb = [dim_map_b.get(d, 0.0) for d in all_dims]
    dot = sum(x * y for x, y in zip(va, vb))
    mag_a = math.sqrt(sum(x * x for x in va))
    mag_b = math.sqrt(sum(x * x for x in vb))
    if mag_a <= 0 or mag_b <= 0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def exhibition_feature_vector(exhibition: Exhibition) -> FeatureVector:
    """Build numeric feature vector from exhibition attributes."""
    dims: list[str] = []
    vals: list[float] = []

    score = exhibition.vitrine_score or 50.0
    crowd = exhibition.crowd_score or 50.0
    dims.extend(["vitrine_score", "crowd_score"])
    vals.extend([score / 100.0, crowd / 100.0])

    arts = exhibition.all_artworks()
    if arts:
        avg_intensity = sum(a.intensity for a in arts) / len(arts)
        avg_tension = sum(a.narrative_tension for a in arts) / len(arts)
        avg_dwell = sum(a.dwell_sec for a in arts) / len(arts)
        dims.extend(["avg_intensity", "avg_tension", "avg_dwell"])
        vals.extend([avg_intensity, avg_tension, min(1.0, avg_dwell / 300.0)])

    if exhibition.genre:
        dims.append(f"genre:{exhibition.genre.lower()}")
        vals.append(1.0)

    signal_kinds = {s.kind.value for s in exhibition.signals}
    for kind in ("review", "visitor", "critic", "social", "sales", "curator"):
        dims.append(f"signal:{kind}")
        vals.append(1.0 if kind in signal_kinds else 0.0)

    return FeatureVector(dims, vals)


def tag_sets(exhibition: Exhibition) -> set[str]:
    tags = {t.label.lower() for t in exhibition.tags}
    for art in exhibition.all_artworks():
        tags.update(t.lower() for t in art.tags)
    return tags


def artwork_feature_vector(artwork: Artwork) -> FeatureVector:
    dims = ["intensity", "narrative_tension", "wall_text_ratio", "dwell"]
    vals = [
        artwork.intensity,
        artwork.narrative_tension,
        artwork.wall_text_ratio,
        min(1.0, artwork.dwell_sec / 300.0),
    ]
    for tag in artwork.tags:
        dims.append(f"tag:{tag.lower()}")
        vals.append(1.0)
    return FeatureVector(dims, vals)


def composite_similarity(a: Exhibition, b: Exhibition, weights: dict[str, float] | None = None) -> SimilarityResult:
    """Composite similarity using cosine features and Jaccard tags."""
    w = weights or {"cosine": 0.35, "jaccard": 0.30, "genre": 0.15, "score": 0.20}

    fv_a = exhibition_feature_vector(a).normalize()
    fv_b = exhibition_feature_vector(b).normalize()
    cos = cosine_similarity(fv_a, fv_b)

    jac = jaccard_similarity(tag_sets(a), tag_sets(b))

    genre_match = 1.0 if a.genre and b.genre and a.genre.lower() == b.genre.lower() else 0.0

    sa = a.vitrine_score or 50.0
    sb = b.vitrine_score or 50.0
    score_prox = max(0.0, 1.0 - abs(sa - sb) / 100.0)

    composite = (
        w["cosine"] * cos
        + w["jaccard"] * jac
        + w["genre"] * genre_match
        + w["score"] * score_prox
    )

    return SimilarityResult(
        score=round(min(1.0, composite), 3),
        cosine_similarity=round(cos, 3),
        jaccard_tags=round(jac, 3),
        genre_match=genre_match,
        score_proximity=round(score_prox, 3),
    )


def rank_similar(
    target: Exhibition,
    candidates: Sequence[Exhibition],
    limit: int = 10,
) -> list[tuple[Exhibition, SimilarityResult]]:
    scored = [(c, composite_similarity(target, c)) for c in candidates if c.id != target.id]
    return sorted(scored, key=lambda x: -x[1].score)[:limit]


def pairwise_similarity_matrix(
    exhibitions: Sequence[Exhibition],
) -> dict[str, dict[str, float]]:
    matrix: dict[str, dict[str, float]] = {}
    for a in exhibitions:
        matrix[a.id] = {}
        for b in exhibitions:
            if a.id == b.id:
                matrix[a.id][b.id] = 1.0
            else:
                matrix[a.id][b.id] = composite_similarity(a, b).score
    return matrix


def find_nearest_neighbors(
    target: Exhibition,
    candidates: Sequence[Exhibition],
    k: int = 5,
    min_score: float = 0.1,
) -> list[tuple[str, float]]:
    ranked = rank_similar(target, candidates, limit=k * 2)
    return [(ex.id, res.score) for ex, res in ranked if res.score >= min_score][:k]
