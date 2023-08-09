"""Snapshot builders for ingest checkpoints."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from vitrine_types.models import Snapshot


@dataclass
class SnapshotBuilder:
    exhibition_id: str
    records: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_record(self, record: dict[str, Any]) -> None:
        self.records.append(record)

    def _checksum(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def build(self, snapshot_id: str | None = None) -> Snapshot:
        payload = {
            "exhibition_id": self.exhibition_id,
            "record_count": len(self.records),
            "records": self.records,
            "metadata": self.metadata,
        }
        sid = snapshot_id or f"snap-{self.exhibition_id}-{len(self.records)}"
        return Snapshot(
            id=sid,
            exhibition_id=self.exhibition_id,
            captured_at=datetime.now(timezone.utc),
            payload=payload,
            checksum=self._checksum(payload),
        )


def diff_snapshots(a: Snapshot, b: Snapshot) -> dict[str, Any]:
    a_ids = {r.get("id") for r in a.payload.get("records", []) if r.get("id")}
    b_ids = {r.get("id") for r in b.payload.get("records", []) if r.get("id")}
    return {
        "added": sorted(b_ids - a_ids),
        "removed": sorted(a_ids - b_ids),
        "checksum_changed": a.checksum != b.checksum,
    }
