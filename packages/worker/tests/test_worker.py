from vitrine_types.models import Job, JobStatus

from vitrine_worker.orchestrator import TokenBucket, WorkerOrchestrator


def test_token_bucket_allows_burst():
    bucket = TokenBucket(rate=1.0, capacity=5.0)
    assert bucket.consume()
    assert bucket.consume()


def test_token_bucket_depletes():
    bucket = TokenBucket(rate=0.0, capacity=1.0)
    assert bucket.consume()
    assert not bucket.consume()


def test_worker_processes_job():
    worker = WorkerOrchestrator()
    worker.register_handler("echo", lambda j: {"payload": j.payload})
    job = Job(id="j1", name="echo", payload={"x": 1})
    worker.submit(job)
    worker.process_one()
    assert worker.stats.processed == 1


def test_worker_fails_without_handler():
    worker = WorkerOrchestrator()
    job = Job(id="j2", name="missing")
    worker.submit(job)
    worker.process_one()
    assert worker.stats.failed == 1


def test_worker_retries_then_dlq():
    worker = WorkerOrchestrator()

    def fail(_job: Job) -> dict:
        raise RuntimeError("boom")

    worker.register_handler("fail", fail)
    job = Job(id="j3", name="fail", max_attempts=2)
    worker.submit(job)
    worker.process_one()
    worker.process_one()
    assert worker.stats.dead_lettered >= 1


def test_worker_event_store_lifecycle():
    worker = WorkerOrchestrator()
    worker.register_handler("ok", lambda j: {})
    job = Job(id="j4", name="ok")
    worker.submit(job)
    worker.process_one()
    events = worker.event_store.replay_job_lifecycle("j4")
    assert len(events) >= 2


def test_worker_rate_limit():
    worker = WorkerOrchestrator()
    worker.rate_limiter = TokenBucket(rate=0.0, capacity=0.0)
    worker.register_handler("x", lambda j: {})
    worker.submit(Job(id="j5", name="x"))
    result = worker.process_one()
    assert result is None
    assert worker.stats.rate_limited == 1
