"""Pytest fixtures for API route smoke tests."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from services.container import ServiceContainer, create_service_container, reset_container


def _build_mock_container() -> ServiceContainer:
    """Return a container whose services yield minimal JSON-serializable payloads."""
    catalog = MagicMock()
    catalog.list_exhibitions.return_value = []
    catalog.get_exhibition.return_value = {"id": "ex-001"}
    catalog.list_tags.return_value = []
    catalog.format_spectrum.return_value = []

    mix = MagicMock()
    mix.pacing.return_value = {"curve": []}
    mix.dialogue.return_value = {"ratio": 0.0}

    crowd = MagicMock()
    crowd.arc.return_value = {"completeness": 1.0}
    crowd.web.return_value = {"nodes": [], "edges": []}
    crowd.theme_clusters.return_value = []

    intelligence = MagicMock()
    intelligence.report.return_value = {"score": 0.0}
    intelligence.command_center.return_value = {"panels": []}
    intelligence.editorial_decision_report.return_value = {"decisions": []}

    editorial = MagicMock()
    editorial.risks.return_value = []
    editorial.publication_windows.return_value = []
    editorial.signals.return_value = []

    enterprise = MagicMock()
    enterprise.program.return_value = {}
    enterprise.budget.return_value = {}
    enterprise.board_pack.return_value = {}
    enterprise.compliance.return_value = {}
    enterprise.incidents.return_value = {}

    graph = MagicMock()
    graph.shortest_path.return_value = {"path": []}
    graph.traverse.return_value = {"visited": []}
    graph.residency_tree.return_value = {"roots": []}

    parser = MagicMock()
    parser.tokenize.return_value = {"tokens": []}
    parser.parse.return_value = {"ast": {}}
    parser.compile.return_value = {"query": ""}

    pipeline = MagicMock()
    pipeline.run.return_value = {"status": "ok"}

    worker = MagicMock()
    worker.batch_score.return_value = {"scores": []}
    worker.ingest.return_value = {"accepted": 0}

    queue = MagicMock()
    queue.list_jobs.return_value = []

    scheduler = MagicMock()
    scheduler.list_schedules.return_value = []

    retry = MagicMock()
    retry.dead_letter_queue.return_value = []
    retry.replay.return_value = {"job_id": "job-1", "status": "replayed"}

    ingest = MagicMock()
    ingest.ingest_snapshot.return_value = {"imported": 0}

    rules = MagicMock()
    rules.run_report.return_value = {"violations": []}

    sync = MagicMock()
    sync.reconcile.return_value = {"diff": []}

    rebalance = MagicMock()
    rebalance.route.return_value = {"route": []}

    ai = MagicMock()
    ai.recommend.return_value = {"items": []}
    ai.similar.return_value = {"items": []}

    events = MagicMock()
    orchestrator = MagicMock()

    return ServiceContainer(
        catalog=catalog,
        mix=mix,
        crowd=crowd,
        intelligence=intelligence,
        editorial=editorial,
        enterprise=enterprise,
        graph=graph,
        parser=parser,
        pipeline=pipeline,
        worker=worker,
        queue=queue,
        scheduler=scheduler,
        retry=retry,
        ingest=ingest,
        rules=rules,
        sync=sync,
        rebalance=rebalance,
        ai=ai,
        events=events,
        orchestrator=orchestrator,
    )


@pytest.fixture(autouse=True)
def mock_service_container(request, monkeypatch):
    """Patch the service container so route tests run without loading seed data."""
    if "test_integration_seed" in request.node.fspath.basename:
        reset_container()
        container = create_service_container()
        monkeypatch.setattr("services.container._container", container)
        monkeypatch.setattr("services.container.get_container", lambda: container)
        monkeypatch.setattr("services.container.create_service_container", lambda: container)
        yield container
        reset_container()
        return

    reset_container()
    container = _build_mock_container()
    monkeypatch.setattr("services.container._container", container)
    monkeypatch.setattr("services.container.get_container", lambda: container)
    monkeypatch.setattr("services.container.create_service_container", lambda: container)
    yield container
    reset_container()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()
