from vitrine_sync.merkle import leaf_diff, merkle_root, reconcile


def test_merkle_root_single():
    root = merkle_root(["a"])
    assert len(root) == 64


def test_merkle_root_deterministic():
    leaves = ["x", "y", "z"]
    assert merkle_root(leaves) == merkle_root(leaves)


def test_merkle_root_empty():
    assert len(merkle_root([])) == 64


def test_leaf_diff_added_removed():
    local = {"a": "1"}
    remote = {"a": "1", "b": "2"}
    diff = leaf_diff(local, remote)
    assert diff.added == ["b"]
    assert diff.removed == []


def test_leaf_diff_changed():
    local = {"a": "old"}
    remote = {"a": "new"}
    diff = leaf_diff(local, remote)
    assert len(diff.changed) == 1


def test_reconcile_prefers_remote():
    local = {"a": "1", "b": "local"}
    remote = {"a": "1", "b": "remote", "c": "new"}
    result = reconcile(local, remote, prefer="remote")
    assert result.merged["b"] == "remote"
    assert "c" in result.merged


def test_reconcile_prefers_local_on_change():
    local = {"a": "local"}
    remote = {"a": "remote"}
    result = reconcile(local, remote, prefer="local")
    assert result.merged["a"] == "local"
