"""Append-only event store with vector clocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class EventType(str, Enum):
    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    SCORE_COMPUTED = "score.computed"
    SCORE_UPDATED = "score.updated"


@dataclass
class VectorClock:
    clocks: dict[str, int] = field(default_factory=dict)

    def increment(self, node_id: str) -> None:
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1

    def merge(self, other: "VectorClock") -> None:
        for k, v in other.clocks.items():
            self.clocks[k] = max(self.clocks.get(k, 0), v)

    def happens_before(self, other: "VectorClock") -> bool:
        if not self.clocks:
            return True
        seen_less = False
        all_keys = set(self.clocks) | set(other.clocks)
        for k in all_keys:
            a, b = self.clocks.get(k, 0), other.clocks.get(k, 0)
            if a > b:
                return False
            if a < b:
                seen_less = True
        return seen_less


@dataclass
class DomainEvent:
    id: str
    event_type: EventType
    aggregate_id: str
    payload: dict[str, Any]
    clock: VectorClock
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventStore:
    """Append-only in-memory event store."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._clock = VectorClock()

    def append(self, event_type: EventType, aggregate_id: str, payload: dict[str, Any], node_id: str = "local") -> DomainEvent:
        self._clock.increment(node_id)
        clock_copy = VectorClock(clocks=dict(self._clock.clocks))
        event = DomainEvent(
            id=str(uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload,
            clock=clock_copy,
        )
        self._events.append(event)
        return event

    def stream(self, aggregate_id: str | None = None, event_type: EventType | None = None) -> list[DomainEvent]:
        out = self._events
        if aggregate_id:
            out = [e for e in out if e.aggregate_id == aggregate_id]
        if event_type:
            out = [e for e in out if e.event_type == event_type]
        return list(out)

    def replay_job_lifecycle(self, job_id: str) -> list[EventType]:
        events = self.stream(aggregate_id=job_id)
        return [e.event_type for e in events]

    @property
    def vector_clock(self) -> VectorClock:
        return VectorClock(clocks=dict(self._clock.clocks))

    def __len__(self) -> int:
        return len(self._events)
