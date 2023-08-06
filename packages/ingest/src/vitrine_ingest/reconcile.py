"""Reconciliation strategies for ingest merges."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ReconcileStrategy(str, Enum):
    REPLACE = "replace"
    MERGE_SHALLOW = "merge_shallow"
    MERGE_DEEP = "merge_deep"
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    MAX_SCORE = "max_score"


@dataclass
class ReconcileResult:
    merged: dict[str, dict[str, Any]]
    added: list[str]
    updated: list[str]
    unchanged: list[str]
    conflicts: list[str]


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, val in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def reconcile_with_strategy(
    local: dict[str, dict[str, Any]],
    remote: dict[str, dict[str, Any]],
    strategy: ReconcileStrategy = ReconcileStrategy.MERGE_SHALLOW,
) -> ReconcileResult:
    merged: dict[str, dict[str, Any]] = {}
    added: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []

    all_keys = set(local) | set(remote)
    for key in all_keys:
        loc = local.get(key)
        rem = remote.get(key)
        if loc is None and rem is not None:
            merged[key] = dict(rem)
            added.append(key)
        elif rem is None and loc is not None:
            merged[key] = dict(loc)
            unchanged.append(key)
        elif loc == rem:
            merged[key] = dict(loc)
            unchanged.append(key)
        else:
            if strategy == ReconcileStrategy.KEEP_LOCAL:
                merged[key] = dict(loc)
            elif strategy == ReconcileStrategy.KEEP_REMOTE:
                merged[key] = dict(rem)
            elif strategy == ReconcileStrategy.REPLACE:
                merged[key] = dict(rem)
            elif strategy == ReconcileStrategy.MERGE_DEEP:
                merged[key] = _deep_merge(loc, rem)
            elif strategy == ReconcileStrategy.MAX_SCORE:
                ls = float(loc.get("score", 0))
                rs = float(rem.get("score", 0))
                merged[key] = dict(rem if rs >= ls else loc)
            else:
                merged[key] = {**loc, **rem}
            if loc != rem:
                updated.append(key)
            if "score" in loc and "score" in rem and loc["score"] != rem["score"]:
                conflicts.append(key)
    return ReconcileResult(merged=merged, added=added, updated=updated, unchanged=unchanged, conflicts=conflicts)
