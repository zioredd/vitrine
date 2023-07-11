from vitrine_rebalance.routing import (
    LRUPathCache,
    WeightedEdge,
    bellman_ford,
    dijkstra_min_fee,
    greedy_rebalance,
)


def test_bellman_ford_no_negative_cycle():
    nodes = ["a", "b", "c"]
    edges = [
        WeightedEdge("a", "b", 1.0),
        WeightedEdge("b", "c", 2.0),
    ]
    dist, cycle = bellman_ford(nodes, edges, "a")
    assert cycle is None
    assert dist["c"] == 3.0


def test_bellman_ford_detects_negative_cycle():
    nodes = ["a", "b", "c"]
    edges = [
        WeightedEdge("a", "b", 1.0),
        WeightedEdge("b", "c", -1.0),
        WeightedEdge("c", "a", -1.0),
    ]
    _dist, cycle = bellman_ford(nodes, edges, "a")
    assert cycle is not None
    assert len(cycle.nodes) >= 2


def test_dijkstra_min_fee():
    adj = {
        "a": [("b", 1.0, 5.0), ("c", 2.0, 1.0)],
        "b": [("d", 1.0, 1.0)],
        "c": [("d", 1.0, 3.0)],
        "d": [],
    }
    path, fee = dijkstra_min_fee(adj, "a", "d")
    assert path[0] == "a" and path[-1] == "d"
    assert fee == 4.0


def test_greedy_rebalance():
    balances = {"A": 120.0, "B": 80.0, "C": 100.0}
    plan = greedy_rebalance(balances, target=100.0, capacity={"A": 50.0, "B": 50.0, "C": 50.0})
    assert plan.total_moved > 0
    assert plan.moves


def test_lru_path_cache_evicts_oldest():
    cache = LRUPathCache(max_size=2)
    cache.put("a", "b", ["a", "b"], 1.0)
    cache.put("b", "c", ["b", "c"], 2.0)
    cache.get("a", "b")
    cache.put("c", "d", ["c", "d"], 3.0)
    assert len(cache) == 2
    assert cache.get("b", "c") is None


def test_lru_cache_hit():
    cache = LRUPathCache()
    cache.put("x", "y", ["x", "y"], 5.0)
    hit = cache.get("x", "y")
    assert hit == (["x", "y"], 5.0)


def test_greedy_rebalance_balanced():
    balances = {"A": 100.0, "B": 100.0}
    plan = greedy_rebalance(balances, target=100.0, capacity={"A": 100.0, "B": 100.0})
    assert plan.total_moved == 0.0
