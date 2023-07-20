"""Regression: min-heap peek returns highest-priority job."""

from datetime import datetime, timezone

from vitrine_queue.heap import MinHeap
from vitrine_types.models import Job, JobStatus


def _job(job_id: str, priority: int) -> Job:
    return Job(
        id=job_id,
        name=f"job-{job_id}",
        status=JobStatus.PENDING,
        priority=priority,
        scheduled_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )


def test_peek_returns_lowest_priority_number():
    heap = MinHeap()
    heap.push(_job("low", 5))
    heap.push(_job("high", 1))
    assert heap.peek().id == "high"
