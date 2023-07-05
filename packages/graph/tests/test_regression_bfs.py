"""Regression: BFS must reach all connected nodes."""

from vitrine_graph.graph import AdjacencyGraph, bfs
from vitrine_types.models import GraphNode


def test_bfs_reaches_all_nodes_in_chain():
    graph = AdjacencyGraph(
        nodes={
            "a": GraphNode(id="a", label="a"),
            "b": GraphNode(id="b", label="b"),
            "c": GraphNode(id="c", label="c"),
        },
        adjacency={
            "a": [("b", 1.0)],
            "b": [("c", 1.0)],
            "c": [],
        },
    )
    order = bfs(graph, "a")
    assert order == ["a", "b", "c"]
