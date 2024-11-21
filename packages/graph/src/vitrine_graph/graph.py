"""Exhibition graph algorithms: BFS, Dijkstra, residency tree."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass, field

from vitrine_types.models import Exhibition, GraphEdge, GraphNode


@dataclass
class AdjacencyGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    adjacency: dict[str, list[tuple[str, float]]] = field(default_factory=dict)


def build_exhibition_graph(exhibition: Exhibition) -> AdjacencyGraph:
    graph = AdjacencyGraph()
    for node in exhibition.graph_nodes:
        graph.nodes[node.id] = node
        graph.adjacency.setdefault(node.id, [])
    for edge in exhibition.graph_edges:
        graph.adjacency.setdefault(edge.source_id, []).append((edge.target_id, edge.weight))
        graph.adjacency.setdefault(edge.target_id, [])
        if edge.target_id not in graph.nodes:
            graph.nodes[edge.target_id] = GraphNode(id=edge.target_id, label=edge.target_id)
        if edge.source_id not in graph.nodes:
            graph.nodes[edge.source_id] = GraphNode(id=edge.source_id, label=edge.source_id)
    return graph


def bfs(graph: AdjacencyGraph, start: str) -> list[str]:
    if start not in graph.adjacency:
        return []
    visited: set[str] = set()
    order: list[str] = []
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for neighbor, _ in graph.adjacency.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order


def dijkstra(graph: AdjacencyGraph, source: str, target: str) -> tuple[list[str], float]:
    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, str | None] = {source: None}
    heap: list[tuple[float, str]] = [(0.0, source)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost > dist.get(node, float("inf")):
            continue
        if node == target:
            break
        for neighbor, weight in graph.adjacency.get(node, []):
            new_cost = cost + weight
            if new_cost < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_cost
                prev[neighbor] = node
                heapq.heappush(heap, (new_cost, neighbor))
    if target not in dist:
        return [], float("inf")
    path: list[str] = []
    cur: str | None = target
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return path, dist[target]


@dataclass
class TreeNode:
    id: str
    label: str
    children: list["TreeNode"] = field(default_factory=list)


def residency_tree(exhibitions: list[Exhibition], residency: str) -> TreeNode:
    root = TreeNode(id=residency, label=residency)
    matching = [e for e in exhibitions if e.residency == residency]
    series_map: dict[str, list[Exhibition]] = {}
    for ex in matching:
        key = ex.series or "ungrouped"
        series_map.setdefault(key, []).append(ex)
    for series, items in sorted(series_map.items()):
        child = TreeNode(id=series, label=series)
        for ex in sorted(items, key=lambda e: e.title):
            child.children.append(TreeNode(id=ex.id, label=ex.title))
        root.children.append(child)
    return root
