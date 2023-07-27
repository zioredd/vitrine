from vitrine_types.models import Job, JobStatus

from vitrine_retry.backoff import BackoffConfig, DeadLetterQueue, compute_backoff, retry_or_dead_letter, should_dead_letter


def test_backoff_grows_exponentially():
    config = BackoffConfig(base_delay_sec=1.0, multiplier=2.0, jitter=0.0)
    d1 = compute_backoff(1, config)
    d2 = compute_backoff(2, config)
    assert d2 >= d1


def test_backoff_capped_at_max():
    config = BackoffConfig(base_delay_sec=10.0, max_delay_sec=50.0, multiplier=10.0, jitter=0.0)
    assert compute_backoff(10, config) <= 50.0


def test_should_dead_letter():
    job = Job(id="j", name="t", attempts=3, max_attempts=3)
    assert should_dead_letter(job)


def test_dlq_push_and_pop():
    dlq = DeadLetterQueue()
    job = Job(id="j", name="t", attempts=3, max_attempts=3)
    dlq.push(job, "max retries")
    assert len(dlq) == 1
    entry = dlq.pop()
    assert entry.reason == "max retries"
    assert job.status == JobStatus.DEAD


def test_retry_or_dead_letter_retries():
    dlq = DeadLetterQueue()
    job = Job(id="j", name="t", attempts=1, max_attempts=3, status=JobStatus.FAILED)
    retry_or_dead_letter(job, dlq, "error")
    assert job.status == JobStatus.PENDING
    assert len(dlq) == 0


def test_retry_or_dead_letter_sends_to_dlq():
    dlq = DeadLetterQueue()
    job = Job(id="j", name="t", attempts=3, max_attempts=3, status=JobStatus.FAILED)
    retry_or_dead_letter(job, dlq, "fatal")
    assert len(dlq) == 1


def test_backoff_non_negative():
    for attempt in range(1, 6):
        assert compute_backoff(attempt) >= 0.0
