from vitrine_types.models import Artwork, Exhibition, GraphEdge, GraphNode, Room

from vitrine_crowd.narrative import (
    arc_completeness,
    relationship_web,
    residency_lens,
    theme_clusters,
)


def test_relationship_web_from_graph():
    ex = Exhibition(
        id="ex",
        title="Web",
        curator="C",
        graph_nodes=[
            GraphNode(id="a", label="A"),
            GraphNode(id="b", label="B"),
        ],
        graph_edges=[GraphEdge(source_id="a", target_id="b", weight=1.0)],
    )
    web = relationship_web(ex)
    assert len(web.edges) == 1
    assert web.density > 0


def test_relationship_web_from_tags():
    ex = Exhibition(
        id="ex",
        title="Tags",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A1", artist="X", tags=["blue"]),
                    Artwork(id="a2", title="A2", artist="Y", tags=["blue"]),
                ],
            )
        ],
    )
    web = relationship_web(ex)
    assert len(web.edges) >= 1


def test_arc_completeness():
    ex = Exhibition(
        id="ex",
        title="Arc",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A", artist="X", position=0, narrative_tension=0.2),
                    Artwork(id="a2", title="B", artist="Y", position=1, narrative_tension=0.8),
                    Artwork(id="a3", title="C", artist="Z", position=2, narrative_tension=0.4),
                ],
            )
        ],
    )
    arc = arc_completeness(ex)
    assert arc.tension_span >= 0.5


def test_theme_clusters():
    ex = Exhibition(
        id="ex",
        title="Themes",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A", artist="X", tags=["light"]),
                    Artwork(id="a2", title="B", artist="Y", tags=["light"]),
                ],
            )
        ],
    )
    clusters = theme_clusters(ex)
    assert len(clusters) == 1
    assert clusters[0].label == "light"


def test_residency_lens():
    exs = [
        Exhibition(id="1", title="A", curator="C", residency="MoCA", series="S1", crowd_score=80),
        Exhibition(id="2", title="B", curator="C", residency="MoCA", series="S2", crowd_score=60),
    ]
    lens = residency_lens(exs, "MoCA")
    assert lens.exhibition_count == 2
    assert lens.avg_crowd_score == 70.0


def test_arc_single_artwork():
    ex = Exhibition(id="x", title="X", curator="C", rooms=[])
    assert arc_completeness(ex).completeness == 0.0


def test_theme_clusters_min_size():
    ex = Exhibition(
        id="ex",
        title="Solo",
        curator="C",
        rooms=[Room(id="r", name="R", artworks=[Artwork(id="a", title="A", artist="X", tags=["solo"])])],
    )
    assert theme_clusters(ex, min_size=2) == []
