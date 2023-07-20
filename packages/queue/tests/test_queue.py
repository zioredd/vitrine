from datetime import datetime, timezone

from vitrine_types.models import Job, JobStatus

from vitrine_queue.heap import JobQueue, JobStateMachine, MinHeap


def test_min_heap_priority_order():
    heap = MinHeap()
    heap.push(Job(id="low", name="l", priority=8))
    heap.push(Job(id="high", name="h", priority=1))
    first = heap.pop()
    assert first is not None
    assert first.id == "high"


def test_min_heap_fifo_same_priority():
    heap = MinHeap()
    heap.push(Job(id="a", name="a", priority=5))
    heap.push(Job(id="b", name="b", priority=5))
    assert heap.pop().id == "a"


def test_job_state_machine_pending_to_running():
    job = Job(id="j", name="test")
    sm = JobStateMachine(job)
    sm.transition(JobStatus.RUNNING)
    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None


def test_job_state_machine_invalid_transition():
    job = Job(id="j", name="test", status=JobStatus.COMPLETED)
    sm = JobStateMachine(job)
    try:
        sm.transition(JobStatus.RUNNING)
        assert False, "Should raise"
    except ValueError:
        pass


def test_failed_to_pending_retry():
    job = Job(id="j", name="test", status=JobStatus.FAILED)
    sm = JobStateMachine(job)
    sm.transition(JobStatus.PENDING)
    assert job.status == JobStatus.PENDING


def test_job_queue_enqueue_dequeue():
    q = JobQueue()
    q.enqueue(Job(id="1", name="a", priority=3))
    q.enqueue(Job(id="2", name="b", priority=1))
    assert q.dequeue().id == "2"


def test_job_failed_increments_attempts():
    job = Job(id="j", name="t", status=JobStatus.RUNNING)
    sm = JobStateMachine(job)
    sm.transition(JobStatus.FAILED, error="timeout")
    assert job.attempts == 1
    assert job.error == "timeout"
