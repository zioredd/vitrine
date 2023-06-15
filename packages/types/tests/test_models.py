from datetime import date, datetime

import pytest
from pydantic import ValidationError

from vitrine_types.models import (
    Artwork,
    Exhibition,
    GraphEdge,
    GraphNode,
    Job,
    JobStatus,
    Provenance,
    Room,
    Signal,
    SignalKind,
    Tag,
    VenueMetadata,
)


def test_exhibition_all_artworks_flattens_rooms():
    ex = Exhibition(
        id="ex-1",
        title="Luminous Fields",
        curator="A. Chen",
        rooms=[
            Room(id="r1", name="North", artworks=[Artwork(id="a1", title="Blue", artist="X")]),
            Room(id="r2", name="South", artworks=[Artwork(id="a2", title="Red", artist="Y")]),
        ],
    )
    assert len(ex.all_artworks()) == 2
    assert {a.id for a in ex.all_artworks()} == {"a1", "a2"}


def test_provenance_confidence_clamped():
    p = Provenance(source_name="ArtForum", confidence=1.0)
    assert p.confidence == 1.0
    with pytest.raises(ValidationError):
        Provenance(source_name="ArtForum", confidence=1.5)


def test_signal_requires_provenance():
    with pytest.raises(ValidationError):
        Signal(id="s1", exhibition_id="ex-1", kind=SignalKind.REVIEW, score=80.0)


def test_job_defaults():
    job = Job(id="j1", name="score-exhibition")
    assert job.status == JobStatus.PENDING
    assert job.max_attempts == 3


def test_graph_structure_roundtrip():
    ex = Exhibition(
        id="ex-2",
        title="Edges",
        curator="B. Lee",
        graph_nodes=[GraphNode(id="n1", label="Entry"), GraphNode(id="n2", label="Exit")],
        graph_edges=[GraphEdge(source_id="n1", target_id="n2", weight=2.5)],
    )
    assert ex.graph_edges[0].weight == 2.5


def test_venue_and_tags():
    ex = Exhibition(
        id="ex-3",
        title="Tagged",
        curator="C. Park",
        tags=[Tag(id="t1", label="contemporary", category="movement")],
        venue=VenueMetadata(name="MoCA", city="Los Angeles", format="museum"),
        opened_on=date(2025, 3, 1),
    )
    assert ex.venue.name == "MoCA"
    assert ex.tags[0].label == "contemporary"
