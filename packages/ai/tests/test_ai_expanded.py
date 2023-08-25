"""Expanded AI module tests."""

from __future__ import annotations

from vitrine_ai.narratives import generate_curator_narrative, narrative_to_markdown
from vitrine_ai.similarity import (
    composite_similarity,
    cosine_similarity,
    exhibition_feature_vector,
    jaccard_similarity,
    rank_similar,
)
from vitrine_ai.transitions import (
    build_transition_matrix,
    optimal_reorder_greedy,
    score_path,
    sequential_transitions,
    transition_entropy,
)
from vitrine_ai.similarity import FeatureVector
from vitrine_catalog.repository import CatalogRepository
from vitrine_types.models import Artwork, Exhibition, Room, Tag


def _exhibitions():
    return CatalogRepository.from_seed().load_all()


def test_cosine_similarity_identical():
    v = FeatureVector(["a", "b"], [1.0, 0.0])
    assert cosine_similarity(v, v) == 1.0


def test_cosine_similarity_orthogonal():
    a = FeatureVector(["x", "y"], [1.0, 0.0])
    b = FeatureVector(["x", "y"], [0.0, 1.0])
    assert cosine_similarity(a, b) == 0.0


def test_jaccard_similarity():
    assert jaccard_similarity({"a", "b"}, {"b", "c"}) == 1 / 3


def test_exhibition_feature_vector():
    ex = _exhibitions()[0]
    fv = exhibition_feature_vector(ex)
    assert len(fv.dimensions) == len(fv.values)


def test_composite_similarity_same_exhibition():
    ex = _exhibitions()[0]
    result = composite_similarity(ex, ex)
    assert result.score > 0.5


def test_rank_similar():
    exs = _exhibitions()
    ranked = rank_similar(exs[0], exs[1:10], limit=5)
    assert len(ranked) <= 5


def test_build_transition_matrix():
    ex = _exhibitions()[0]
    matrix = build_transition_matrix(ex)
    assert matrix.size == len(ex.all_artworks())
    assert matrix.avg_score >= 0


def test_sequential_transitions():
    ex = _exhibitions()[0]
    cells = sequential_transitions(ex)
    arts = ex.all_artworks()
    assert len(cells) == max(0, len(arts) - 1)


def test_score_path():
    arts = sorted(_exhibitions()[0].all_artworks(), key=lambda a: a.position)
    path = score_path(arts)
    assert path.avg_transition >= 0


def test_optimal_reorder_greedy():
    ex = _exhibitions()[0]
    order = optimal_reorder_greedy(ex)
    assert len(order) == len(ex.all_artworks())


def test_transition_entropy():
    ex = _exhibitions()[0]
    entropy = transition_entropy(ex)
    assert entropy >= 0


def test_generate_curator_narrative():
    ex = _exhibitions()[0]
    narrative = generate_curator_narrative(ex, tone="formal")
    assert narrative.exhibition_id == ex.id
    assert len(narrative.sections) >= 3


def test_narrative_to_markdown():
    ex = _exhibitions()[0]
    md = narrative_to_markdown(generate_curator_narrative(ex))
    assert ex.title in md
    assert "#" in md
