from vitrine_events.store import EventStore, EventType, VectorClock


def test_append_increments_clock():
    store = EventStore()
    store.append(EventType.JOB_CREATED, "job-1", {"name": "score"})
    assert store.vector_clock.clocks["local"] == 1


def test_job_lifecycle_replay():
    store = EventStore()
    store.append(EventType.JOB_CREATED, "j1", {})
    store.append(EventType.JOB_STARTED, "j1", {})
    store.append(EventType.JOB_COMPLETED, "j1", {"result": 85})
    lifecycle = store.replay_job_lifecycle("j1")
    assert lifecycle == [EventType.JOB_CREATED, EventType.JOB_STARTED, EventType.JOB_COMPLETED]


def test_stream_filter_by_type():
    store = EventStore()
    store.append(EventType.SCORE_COMPUTED, "ex-1", {"score": 90})
    store.append(EventType.JOB_FAILED, "j2", {})
    scores = store.stream(event_type=EventType.SCORE_COMPUTED)
    assert len(scores) == 1


def test_vector_clock_happens_before():
    a = VectorClock({"n1": 1, "n2": 1})
    b = VectorClock({"n1": 2, "n2": 1})
    assert a.happens_before(b)


def test_vector_clock_not_happens_before_concurrent():
    a = VectorClock({"n1": 2, "n2": 1})
    b = VectorClock({"n1": 1, "n2": 2})
    assert not a.happens_before(b)
    assert not b.happens_before(a)


def test_event_store_length():
    store = EventStore()
    store.append(EventType.JOB_CREATED, "j", {})
    store.append(EventType.SCORE_UPDATED, "ex", {"score": 70})
    assert len(store) == 2


def test_clock_merge():
    a = VectorClock({"n1": 3})
    b = VectorClock({"n2": 2})
    a.merge(b)
    assert a.clocks["n1"] == 3
    assert a.clocks["n2"] == 2
