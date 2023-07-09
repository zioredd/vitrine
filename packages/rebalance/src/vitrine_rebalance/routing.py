"""Bellman-Ford, min-fee Dijkstra, greedy planner, LRU path cache."""

from __future__ import annotations

import heapq
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class WeightedEdge:
    source: str
    target: str
    weight: float
    fee: float = 0.0


@dataclass
class NegativeCycle:
    nodes: list[str]
    total_weight: float


def bellman_ford(
    nodes: list[str], edges: list[WeightedEdge], source: str
) -> tuple[dict[str, float], NegativeCycle | None]:
    dist = {n: float("inf") for n in nodes}
    dist[source] = 0.0
    predecessor: dict[str, str | None] = {source: None}
    for _ in range(len(nodes) - 1):
        updated = False
        for e in edges:
            if dist[e.source] + e.weight < dist[e.target]:
                dist[e.target] = dist[e.source] + e.weight
                predecessor[e.target] = e.source
                updated = True
        if not updated:
            break
    for e in edges:
        if dist[e.source] + e.weight < dist[e.target]:
            cycle = _extract_cycle(e.target, predecessor)
            total = sum(
                ed.weight
                for ed in edges
                if ed.source in cycle and ed.target in cycle
            )
            return dist, NegativeCycle(nodes=cycle, total_weight=total)
    return dist, None


def _extract_cycle(start: str, pred: dict[str, str | None]) -> list[str]:
    visited: set[str] = set()
    node: str | None = start
    for _ in range(len(pred) + 1):
        if node is None:
            break
        if node in visited:
            cycle_start = node
            path = [cycle_start]
            cur = pred.get(cycle_start)
            while cur and cur != cycle_start:
                path.append(cur)
                cur = pred.get(cur)
            path.reverse()
            return path
        visited.add(node)
        node = pred.get(node)
    return [start]


def dijkstra_min_fee(
    adjacency: dict[str, list[tuple[str, float, float]]],
    source: str,
    target: str,
) -> tuple[list[str], float]:
    """Dijkstra optimizing fee (second weight), breaking ties by hop count."""
    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, str | None] = {source: None}
    heap: list[tuple[float, str]] = [(0.0, source)]
    while heap:
        fee, node = heapq.heappop(heap)
        if fee > dist.get(node, float("inf")):
            continue
        if node == target:
            break
        for neighbor, _weight, edge_fee in adjacency.get(node, []):
            new_fee = fee + edge_fee
            if new_fee < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_fee
                prev[neighbor] = node
                heapq.heappush(heap, (new_fee, neighbor))
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
class RebalanceMove:
    from_node: str
    to_node: str
    amount: float


@dataclass
class RebalancePlan:
    moves: list[RebalanceMove] = field(default_factory=list)
    total_moved: float = 0.0


def greedy_rebalance(balances: dict[str, float], target: float, capacity: dict[str, float]) -> RebalancePlan:
    """Greedy planner: move surplus from overweight nodes to underweight."""
    plan = RebalancePlan()
    surplus = {k: max(0.0, v - target) for k, v in balances.items()}
    deficit = {k: max(0.0, target - v) for k, v in balances.items()}
    for src, amount in sorted(surplus.items(), key=lambda x: -x[1]):
        remaining = min(amount, capacity.get(src, amount))
        for dst, need in sorted(deficit.items(), key=lambda x: -x[1]):
            if need <= 0 or src == dst:
                continue
            move = min(remaining, need, capacity.get(dst, need))
            if move <= 0:
                continue
            plan.moves.append(RebalanceMove(from_node=src, to_node=dst, amount=round(move, 4)))
            plan.total_moved += move
            remaining -= move
            deficit[dst] -= move
            if remaining <= 0:
                break
    plan.total_moved = round(plan.total_moved, 4)
    return plan


class LRUPathCache:
    def __init__(self, max_size: int = 128) -> None:
        self.max_size = max_size
        self._cache: OrderedDict[tuple[str, str], tuple[list[str], float]] = OrderedDict()

    def get(self, source: str, target: str) -> tuple[list[str], float] | None:
        key = (source, target)
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def put(self, source: str, target: str, path: list[str], cost: float) -> None:
        key = (source, target)
        self._cache[key] = (path, cost)
        self._cache.move_to_end(key)
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)
