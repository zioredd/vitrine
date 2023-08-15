"""Extended rules checks tests."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from vitrine_rules.checks_extended import (
    check_date_range,
    check_graph_connectivity,
    check_signal_freshness,
    check_tag_density,
    check_venue_consistency,
    run_extended_checks,
)
from vitrine_rules.engine import DEFAULT_RULES, run_rules
from vitrine_types.models import (
    Artwork,
    Exhibition,
    GraphEdge,
    GraphNode,
    Provenance,
    Room,
    Signal,
    SignalKind,
    Tag,
    VenueMetadata,
)


def _base_ex(**kwargs) -> Exhibition:
    defaults = {"id": "ex-t", "title": "Test Exhibition", "curator": "Curator"}
    defaults.update(kwargs)
    return Exhibition(**defaults)


def test_venue_consistency_missing():
    violations = check_venue_consistency(_base_ex())
    assert any(v.rule == "venue_consistency" for v in violations)


def test_venue_consistency_valid():
    ex = _base_ex(venue=VenueMetadata(name="Gallery One", city="NYC", country="US"))
    violations = check_venue_consistency(ex)
    assert not any(v.severity.value == "error" for v in violations)


def test_date_range_inverted():
    ex = _base_ex(opened_on=date(2026, 6, 1), closed_on=date(2026, 1, 1))
    violations = check_date_range(ex)
    assert any(v.severity.value == "error" for v in violations)


def test_date_range_valid():
    ex = _base_ex(opened_on=date(2026, 1, 1), closed_on=date(2026, 3, 1))
    violations = check_date_range(ex)
    assert not any(v.severity.value == "error" for v in violations)


def test_tag_density_low():
    ex = _base_ex(
        rooms=[Room(id="r", name="R", artworks=[Artwork(id="a", title="A", artist="X") for _ in range(5)])],
        tags=[],
    )
    violations = check_tag_density(ex)
    assert any(v.rule == "tag_density" for v in violations)


def test_tag_density_with_tags():
    ex = _base_ex(
        tags=[Tag(id="t1", label="modern"), Tag(id="t2", label="abstract")],
        rooms=[Room(id="r", name="R", artworks=[Artwork(id="a", title="A", artist="X", tags=["modern"])])],
    )
    violations = check_tag_density(ex)
    assert isinstance(violations, list)


def test_graph_connectivity_disconnected():
    ex = _base_ex(
        graph_nodes=[GraphNode(id="n1", label="A"), GraphNode(id="n2", label="B")],
        graph_edges=[],
    )
    violations = check_graph_connectivity(ex)
    assert any(v.rule == "graph_connectivity" for v in violations)


def test_graph_connectivity_connected():
    ex = _base_ex(
        graph_nodes=[GraphNode(id="n1", label="A"), GraphNode(id="n2", label="B")],
        graph_edges=[GraphEdge(source_id="n1", target_id="n2")],
    )
    violations = check_graph_connectivity(ex)
    assert not any("disconnected" in v.message for v in violations)


def test_signal_freshness_stale():
    old = datetime.now(timezone.utc) - timedelta(days=400)
    ex = _base_ex(
        signals=[
            Signal(
                id="s1",
                exhibition_id="ex-t",
                kind=SignalKind.REVIEW,
                score=80,
                provenance=Provenance(source_name="X", confidence=0.9, captured_at=old),
            )
        ]
    )
    violations = check_signal_freshness(ex, max_age_days=365)
    assert any(v.rule == "signal_freshness" for v in violations)


def test_signal_freshness_fresh():
    recent = datetime.now(timezone.utc) - timedelta(days=10)
    ex = _base_ex(
        signals=[
            Signal(
                id="s1",
                exhibition_id="ex-t",
                kind=SignalKind.REVIEW,
                score=80,
                provenance=Provenance(source_name="X", confidence=0.9, captured_at=recent),
            ),
            Signal(
                id="s2",
                exhibition_id="ex-t",
                kind=SignalKind.VISITOR,
                score=75,
                provenance=Provenance(source_name="Y", confidence=0.8, captured_at=recent),
            ),
        ]
    )
    violations = check_signal_freshness(ex)
    assert not any(v.severity.value == "error" for v in violations)


def test_run_extended_checks_batch():
    violations = run_extended_checks([_base_ex(), _base_ex(id="ex-t2")])
    assert isinstance(violations, list)


def test_default_rules_include_extended():
    assert check_venue_consistency in DEFAULT_RULES
    assert check_date_range in DEFAULT_RULES


def test_run_rules_with_extended_on_seed():
    from vitrine_catalog.repository import CatalogRepository

    result = run_rules(CatalogRepository.from_seed().load_all()[:3])
    assert isinstance(result.severity_counts, dict)
