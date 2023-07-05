from vitrine_types.models import Exhibition, GraphEdge, GraphNode

from vitrine_graph.graph import AdjacencyGraph, bfs, build_exhibition_graph, dijkstra, residency_tree


def test_bfs_and_dijkstra():
    ex = Exhibition(
        id="g1",
        title="Graph",
        curator="C",
        graph_nodes=[
            GraphNode(id="a", label="A"),
            GraphNode(id="b", label="B"),
            GraphNode(id="c", label="C"),
        ],
        graph_edges=[
            GraphEdge(source_id="a", target_id="b", weight=1.0),
            GraphEdge(source_id="b", target_id="c", weight=2.0),
        ],
    )
    g = build_exhibition_graph(ex)
    assert bfs(g, "a") == ["a", "b", "c"]
    path, cost = dijkstra(g, "a", "c")
    assert path == ["a", "b", "c"]
    assert cost == 3.0


def test_residency_tree_groups_series():
    exs = [
        Exhibition(id="e1", title="Show A", curator="C", residency="MoCA", series="Spring"),
        Exhibition(id="e2", title="Show B", curator="C", residency="MoCA", series="Spring"),
    ]
    tree = residency_tree(exs, "MoCA")
    assert len(tree.children) == 1
    assert len(tree.children[0].children) == 2


def test_dijkstra_unreachable():
    g = AdjacencyGraph(adjacency={"a": [], "b": []})
    path, cost = dijkstra(g, "a", "b")
    assert path == []
    assert cost == float("inf")


def test_bfs_empty_start():
    g = AdjacencyGraph()
    assert bfs(g, "missing") == []


def test_build_graph_infers_nodes_from_edges():
    ex = Exhibition(
        id="g2",
        title="Edges only",
        curator="C",
        graph_edges=[GraphEdge(source_id="x", target_id="y", weight=1.0)],
    )
    g = build_exhibition_graph(ex)
    assert "x" in g.nodes
    assert "y" in g.nodes


def test_dijkstra_shortest_of_two_paths():
    ex = Exhibition(
        id="g3",
        title="Branch",
        curator="C",
        graph_nodes=[
            GraphNode(id="s", label="S"),
            GraphNode(id="m", label="M"),
            GraphNode(id="t", label="T"),
        ],
        graph_edges=[
            GraphEdge(source_id="s", target_id="m", weight=10.0),
            GraphEdge(source_id="m", target_id="t", weight=1.0),
            GraphEdge(source_id="s", target_id="t", weight=5.0),
        ],
    )
    g = build_exhibition_graph(ex)
    path, cost = dijkstra(g, "s", "t")
    assert cost == 5.0
    assert path == ["s", "t"]


def test_residency_tree_empty():
    tree = residency_tree([], "Empty")
    assert tree.id == "Empty"
    assert tree.children == []
