"""Merkle root builder and leaf diff/reconcile."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def _hash_pair(left: str, right: str) -> str:
    return hashlib.sha256(f"{left}|{right}".encode()).hexdigest()


def _hash_leaf(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def merkle_root(leaves: list[str]) -> str:
    """Build Merkle root from ordered leaf strings."""
    if not leaves:
        return _hash_leaf("")
    layer = [_hash_leaf(leaf) for leaf in leaves]
    while len(layer) > 1:
        next_layer: list[str] = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i + 1] if i + 1 < len(layer) else layer[i]
            next_layer.append(_hash_pair(left, right))
        layer = next_layer
    return layer[0]


@dataclass
class LeafDiff:
    added: list[str]
    removed: list[str]
    changed: list[tuple[str, str, str]]  # key, old_hash, new_hash


def leaf_diff(
    local: dict[str, str],
    remote: dict[str, str],
) -> LeafDiff:
    """Diff two leaf maps (key -> content)."""
    added = sorted(k for k in remote if k not in local)
    removed = sorted(k for k in local if k not in remote)
    changed: list[tuple[str, str, str]] = []
    for key in sorted(set(local) & set(remote)):
        local_hash = _hash_leaf(local[key])
        remote_hash = _hash_leaf(remote[key])
        if local_hash != remote_hash:
            changed.append((key, local_hash, remote_hash))
    return LeafDiff(added=added, removed=removed, changed=changed)


@dataclass
class ReconcileResult:
    merged: dict[str, str]
    applied: list[str]


def reconcile(
    local: dict[str, str],
    remote: dict[str, str],
    prefer: str = "remote",
) -> ReconcileResult:
    """Merge leaf maps; on conflict use prefer ('local' or 'remote')."""
    diff = leaf_diff(local, remote)
    merged = dict(local)
    applied: list[str] = []
    for key in diff.added:
        merged[key] = remote[key]
        applied.append(f"add:{key}")
    for key in diff.removed:
        if prefer == "remote":
            merged.pop(key, None)
            applied.append(f"remove:{key}")
    for key, _old, _new in diff.changed:
        merged[key] = remote[key] if prefer == "remote" else local[key]
        applied.append(f"change:{key}")
    return ReconcileResult(merged=merged, applied=applied)
