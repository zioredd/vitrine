"""Binary min-heap priority queue and job state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from vitrine_types.models import Job, JobStatus


class MinHeap:
    """Binary min-heap keyed by (priority, scheduled_at, job_id). Lower priority number = higher urgency."""

    def __init__(self) -> None:
        self._heap: list[tuple[int, float, str, Job]] = []

    def _parent(self, i: int) -> int:
        return (i - 1) // 2

    def _left(self, i: int) -> int:
        return 2 * i + 1

    def _right(self, i: int) -> int:
        return 2 * i + 2

    def _swap(self, i: int, j: int) -> None:
        self._heap[i], self._heap[j] = self._heap[j], self._heap[i]

    def _sift_up(self, i: int) -> None:
        while i > 0:
            p = self._parent(i)
            if self._heap[i] < self._heap[p]:
                self._swap(i, p)
                i = p
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._heap)
        while True:
            smallest = i
            left = self._left(i)
            right = self._right(i)
            if left < n and self._heap[left] < self._heap[smallest]:
                smallest = left
            if right < n and self._heap[right] < self._heap[smallest]:
                smallest = right
            if smallest == i:
                break
            self._swap(i, smallest)
            i = smallest

    def push(self, job: Job) -> None:
        ts = job.scheduled_at.timestamp() if job.scheduled_at else 0.0
        entry = (job.priority, ts, job.id, job)
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def pop(self) -> Job | None:
        if not self._heap:
            return None
        root = self._heap[0][3]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return root

    def peek(self) -> Job | None:
        return self._heap[-1][3] if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)


# Job state machine transitions
_VALID_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.RUNNING, JobStatus.DEAD},
    JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED},
    JobStatus.FAILED: {JobStatus.PENDING, JobStatus.DEAD},
    JobStatus.COMPLETED: set(),
    JobStatus.DEAD: set(),
}


class JobStateMachine:
    def __init__(self, job: Job) -> None:
        self.job = job

    def can_transition(self, new_status: JobStatus) -> bool:
        return new_status in _VALID_TRANSITIONS.get(self.job.status, set())

    def transition(self, new_status: JobStatus, error: str | None = None) -> Job:
        if not self.can_transition(new_status):
            raise ValueError(f"Invalid transition {self.job.status} -> {new_status}")
        now = datetime.now(timezone.utc)
        self.job.status = new_status
        if new_status == JobStatus.RUNNING:
            self.job.started_at = now
        if new_status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.DEAD):
            self.job.finished_at = now
        if error:
            self.job.error = error
        if new_status == JobStatus.FAILED:
            self.job.attempts += 1
        return self.job


@dataclass
class JobQueue:
    heap: MinHeap = field(default_factory=MinHeap)

    def enqueue(self, job: Job) -> None:
        if job.status != JobStatus.PENDING:
            raise ValueError("Can only enqueue pending jobs")
        self.heap.push(job)

    def dequeue(self) -> Job | None:
        return self.heap.pop()

    def pending_count(self) -> int:
        return len(self.heap)
