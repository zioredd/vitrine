"""Multi-stage pipeline runner and snapshot diff."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from vitrine_ingest.pipeline import run_ingest_pipeline
from vitrine_types.models import Snapshot


StageFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class StageResult:
    name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PipelineContext:
    data: dict[str, Any] = field(default_factory=dict)
    stages_run: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def decode_stage(ctx: PipelineContext) -> PipelineContext:
    raw = ctx.data.get("raw_records", [])
    ctx.data["decoded"] = raw
    ctx.stages_run.append("decode")
    return ctx


def normalize_stage(ctx: PipelineContext) -> PipelineContext:
    decoded = ctx.data.get("decoded", [])
    result = run_ingest_pipeline(decoded, required=ctx.data.get("required", ["id"]))
    ctx.data["normalized"] = result.records
    ctx.data["validation_errors"] = [{"field": e.field, "message": e.message} for e in result.errors]
    ctx.stages_run.append("normalize")
    return ctx


def snapshot_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compute key-level diff between two snapshot payloads."""
    added = {k: after[k] for k in after if k not in before}
    removed = {k: before[k] for k in before if k not in after}
    changed = {
        k: {"before": before[k], "after": after[k]}
        for k in before
        if k in after and before[k] != after[k]
    }
    return {"added": added, "removed": removed, "changed": changed}


def make_snapshot(exhibition_id: str, payload: dict[str, Any]) -> Snapshot:
    return Snapshot(
        id=f"snap-{exhibition_id}-{len(payload)}",
        exhibition_id=exhibition_id,
        captured_at=datetime.now(timezone.utc),
        payload=payload,
    )


class StageRunner:
    def __init__(self, stages: list[tuple[str, StageFn]] | None = None) -> None:
        self.stages = stages or [
            ("decode", lambda ctx: decode_stage(ctx)),
            ("normalize", lambda ctx: normalize_stage(ctx)),
        ]

    def run(self, initial: dict[str, Any]) -> PipelineContext:
        ctx = PipelineContext(data=dict(initial))
        for name, fn in self.stages:
            try:
                ctx = fn(ctx)
            except Exception as exc:  # noqa: BLE001
                ctx.errors.append(f"{name}: {exc}")
                break
        return ctx
