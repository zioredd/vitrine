"""Expanded crowd module tests."""

from __future__ import annotations

from vitrine_catalog.repository import CatalogRepository
from vitrine_crowd.arc_variants import (
    ArcModel,
    arc_model_score,
    compare_arc_variants,
    recommend_arc_model,
    score_three_act,
)
from vitrine_crowd.clustering import find_optimal_k, kmeans_theme_clusters, merge_small_clusters
from vitrine_crowd.narrative import arc_completeness, relationship_web, theme_clusters


def _exhibitions():
    return CatalogRepository.from_seed().load_all()


def test_kmeans_theme_clusters():
    ex = _exhibitions()[0]
    report = kmeans_theme_clusters(ex, k=3)
    assert report.k == 3
    assert len(report.clusters) >= 1


def test_find_optimal_k():
    ex = _exhibitions()[0]
    best_k, inertias = find_optimal_k(ex)
    assert best_k >= 1
    assert len(inertias) >= 1


def test_merge_small_clusters():
    ex = _exhibitions()[0]
    report = kmeans_theme_clusters(ex, k=4)
    merged = merge_small_clusters(report, min_size=3)
    assert merged.k <= report.k


def test_score_three_act():
    tensions = [0.2, 0.3, 0.5, 0.7, 0.8, 0.6, 0.4]
    result = score_three_act(tensions)
    assert result.model == ArcModel.THREE_ACT
    assert 0 <= result.score <= 1


def test_compare_arc_variants():
    ex = _exhibitions()[0]
    comparison = compare_arc_variants(ex)
    assert comparison.best_model in ArcModel
    assert len(comparison.variants) == 3


def test_arc_model_score():
    ex = _exhibitions()[0]
    score = arc_model_score(ex, ArcModel.WAVE)
    assert score.model == ArcModel.WAVE


def test_recommend_arc_model():
    ex = _exhibitions()[0]
    model, rec = recommend_arc_model(ex)
    assert isinstance(rec, str)


def test_arc_completeness_seed():
    ex = _exhibitions()[0]
    report = arc_completeness(ex)
    assert 0 <= report.completeness <= 1.5


def test_relationship_web_seed():
    ex = _exhibitions()[0]
    web = relationship_web(ex)
    assert len(web.nodes) > 0


def test_theme_clusters_seed():
    ex = _exhibitions()[0]
    clusters = theme_clusters(ex)
    assert isinstance(clusters, list)
