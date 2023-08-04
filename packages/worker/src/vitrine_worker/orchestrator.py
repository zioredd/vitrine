"""Worker orchestrator: heap + DLQ + event bus + token bucket rate limit."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from vitrine_events.store import EventStore, EventType
from vitrine_queue.heap import JobQueue, JobStateMachine
from vitrine_retry.backoff import DeadLetterQueue, compute_backoff, retry_or_dead_letter
from vitrine_types.models import Job, JobStatus


Handler = Callable[[Job], dict[str, Any]]


class TokenBucket:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, capacity: float) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def consume(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


@dataclass
class WorkerStats:
    processed: int = 0
    failed: int = 0
    dead_lettered: int = 0
    rate_limited: int = 0


@dataclass
class WorkerOrchestrator:
    queue: JobQueue = field(default_factory=JobQueue)
    dlq: DeadLetterQueue = field(default_factory=DeadLetterQueue)
    event_store: EventStore = field(default_factory=EventStore)
    rate_limiter: TokenBucket = field(default_factory=lambda: TokenBucket(rate=10.0, capacity=10.0))
    stats: WorkerStats = field(default_factory=WorkerStats)
    handlers: dict[str, Handler] = field(default_factory=dict)

    def register_handler(self, job_name: str, handler: Handler) -> None:
        self.handlers[job_name] = handler

    def submit(self, job: Job) -> None:
        self.event_store.append(EventType.JOB_CREATED, job.id, {"name": job.name})
        self.queue.enqueue(job)

    def process_one(self) -> Job | None:
        if not self.rate_limiter.consume():
            self.stats.rate_limited += 1
            return None
        job = self.queue.dequeue()
        if job is None:
            return None
        sm = JobStateMachine(job)
        sm.transition(JobStatus.RUNNING)
        self.event_store.append(EventType.JOB_STARTED, job.id, {})
        handler = self.handlers.get(job.name)
        if handler is None:
            sm.transition(JobStatus.FAILED, error="no handler")
            self._handle_failure(job)
            return job
        try:
            result = handler(job)
            sm.transition(JobStatus.COMPLETED)
            self.event_store.append(EventType.JOB_COMPLETED, job.id, result)
            self.stats.processed += 1
        except Exception as exc:  # noqa: BLE001
            sm.transition(JobStatus.FAILED, error=str(exc))
            self._handle_failure(job)
        return job

    def _handle_failure(self, job: Job) -> None:
        self.stats.failed += 1
        self.event_store.append(EventType.JOB_FAILED, job.id, {"error": job.error, "attempts": job.attempts})
        retry_or_dead_letter(job, self.dlq, job.error or "unknown")
        if job.status == JobStatus.DEAD:
            self.stats.dead_lettered += 1
        elif job.status == JobStatus.PENDING:
            delay = compute_backoff(job.attempts)
            job.payload["_retry_delay"] = delay
            self.queue.enqueue(job)

    def drain(self, max_jobs: int = 100) -> int:
        count = 0
        for _ in range(max_jobs):
            if self.process_one() is None and self.queue.pending_count() == 0:
                break
            count += 1
        return count
