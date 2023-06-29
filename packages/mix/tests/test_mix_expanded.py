"""Expanded mix module tests."""

from __future__ import annotations

from vitrine_catalog.repository import CatalogRepository
from vitrine_mix.craft import build_craft_report, energy_map, pacing_curve, pacing_score
from vitrine_mix.energy_analysis import (
    analyze_energy_profile,
    build_energy_gradient_map,
    smoothness_score,
    zone_transition_summary,
)
from vitrine_mix.transition_matrix import (
    build_mix_transition_matrix,
    matrix_entropy,
    matrix_to_nested_list,
    sequential_matrix,
)


def _exhibition():
    return CatalogRepository.from_seed().load_all()[0]


def test_pacing_curve_has_points():
    ex = _exhibition()
    curve = pacing_curve(ex.all_artworks())
    assert len(curve) == len(ex.all_artworks())
    assert curve[0].position >= 0


def test_energy_map_zones():
    ex = _exhibition()
    zones = energy_map(ex.all_artworks(), zone_size=3)
    assert len(zones) >= 1
    assert zones[0].label in ("peak", "valley", "mid")


def test_build_craft_report():
    ex = _exhibition()
    report = build_craft_report(ex)
    assert 0 <= report.pacing_score <= 100


def test_build_energy_gradient_map():
    ex = _exhibition()
    grad_map = build_energy_gradient_map(ex.all_artworks())
    assert len(grad_map.points) == len(ex.all_artworks())
    assert grad_map.avg_intensity >= 0


def test_analyze_energy_profile():
    ex = _exhibition()
    profile = analyze_energy_profile(ex)
    assert profile.exhibition_id == ex.id
    assert len(profile.recommendations) >= 1


def test_smoothness_score():
    ex = _exhibition()
    profile = analyze_energy_profile(ex)
    score = smoothness_score(profile)
    assert 0 <= score <= 100


def test_zone_transition_summary():
    ex = _exhibition()
    profile = analyze_energy_profile(ex)
    summary = zone_transition_summary(profile)
    assert isinstance(summary, list)


def test_build_mix_transition_matrix():
    ex = _exhibition()
    matrix = build_mix_transition_matrix(ex)
    assert matrix.size == len(ex.all_artworks())
    assert len(matrix.entries) > 0


def test_sequential_matrix():
    ex = _exhibition()
    matrix = sequential_matrix(ex)
    assert matrix.size == len(ex.all_artworks())


def test_matrix_to_nested_list():
    ex = _exhibition()
    matrix = build_mix_transition_matrix(ex)
    grid = matrix_to_nested_list(matrix)
    assert len(grid) == matrix.size


def test_matrix_entropy():
    ex = _exhibition()
    matrix = build_mix_transition_matrix(ex)
    entropy = matrix_entropy(matrix)
    assert entropy >= 0


def test_pacing_score_bounded():
    ex = _exhibition()
    score = pacing_score(ex.all_artworks())
    assert 0 <= score <= 100
