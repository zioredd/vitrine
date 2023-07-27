"""Exponential backoff with jitter and dead-letter queue."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from vitrine_types.models import Job, JobStatus


@dataclass
class BackoffConfig:
    base_delay_sec: float = 1.0
    max_delay_sec: float = 300.0
    multiplier: float = 2.0
    jitter: float = 0.25


def compute_backoff(attempt: int, config: BackoffConfig | None = None) -> float:
    """Exponential backoff with multiplicative jitter."""
    config = config or BackoffConfig()
    delay = config.base_delay_sec * (config.multiplier ** max(0, attempt - 1))
    delay = min(delay, config.max_delay_sec)
    jitter_range = delay * config.jitter
    delay += random.uniform(-jitter_range, jitter_range)
    return max(0.0, round(delay, 3))


@dataclass
class DeadLetterEntry:
    job: Job
    reason: str
    dead_at_attempt: int


class DeadLetterQueue:
    def __init__(self) -> None:
        self._entries: list[DeadLetterEntry] = []

    def push(self, job: Job, reason: str) -> None:
        job.status = JobStatus.DEAD
        self._entries.append(DeadLetterEntry(job=job, reason=reason, dead_at_attempt=job.attempts))

    def pop(self) -> DeadLetterEntry | None:
        return self._entries.pop(0) if self._entries else None

    def all(self) -> list[DeadLetterEntry]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)


def should_dead_letter(job: Job) -> bool:
    return job.attempts >= job.max_attempts


def retry_or_dead_letter(job: Job, dlq: DeadLetterQueue, reason: str) -> Job:
    if should_dead_letter(job):
        dlq.push(job, reason)
    else:
        job.status = JobStatus.PENDING
    return job
