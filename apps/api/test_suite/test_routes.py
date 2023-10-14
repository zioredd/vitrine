"""Parametrized smoke tests for all /v1/ API routes."""
from __future__ import annotations

import pytest

SAMPLE_SET_ID = "ex-001"
SAMPLE_BODY = {"expression": "genre:jazz AND bpm:120"}


ROUTE_CASES = [
    pytest.param("get", "/v1/weave", None, id="catalog-weave"),
    pytest.param("get", f"/v1/sets/{SAMPLE_SET_ID}", None, id="catalog-set-detail"),
    pytest.param("get", f"/v1/exhibitions/{SAMPLE_SET_ID}", None, id="catalog-exhibition-detail"),
    pytest.param("get", "/v1/tags", None, id="catalog-tags"),
    pytest.param("get", "/v1/format-spectrum", None, id="catalog-format-spectrum"),
    pytest.param("get", f"/v1/sets/{SAMPLE_SET_ID}/craft/pacing", None, id="mix-craft-pacing"),
    pytest.param("get", f"/v1/sets/{SAMPLE_SET_ID}/craft/dialogue", None, id="mix-craft-dialogue"),
    pytest.param("get", f"/v1/sets/{SAMPLE_SET_ID}/narrative/arc", None, id="crowd-narrative-arc"),
    pytest.param("get", f"/v1/sets/{SAMPLE_SET_ID}/narrative/web", None, id="crowd-narrative-web"),
    pytest.param("get", "/v1/themes/clusters", None, id="crowd-theme-clusters"),
    pytest.param("get", "/v1/intelligence", None, id="intelligence-report"),
    pytest.param("get", "/v1/command-center", None, id="intelligence-command-center"),
    pytest.param("get", "/v1/editorial-decision-report", None, id="intelligence-editorial-decision"),
    pytest.param("get", "/v1/risks", None, id="editorial-risks"),
    pytest.param("get", "/v1/publication-windows", None, id="editorial-publication-windows"),
    pytest.param("get", "/v1/editorial-signals", None, id="editorial-signals"),
    pytest.param("get", "/v1/enterprise/program", None, id="enterprise-program"),
    pytest.param("get", "/v1/enterprise/budget", None, id="enterprise-budget"),
    pytest.param("get", "/v1/enterprise/board-pack", None, id="enterprise-board-pack"),
    pytest.param("get", "/v1/enterprise/compliance", None, id="enterprise-compliance"),
    pytest.param("get", "/v1/enterprise/incidents", None, id="enterprise-incidents"),
    pytest.param("get", f"/v1/graph/sets/{SAMPLE_SET_ID}/path", None, id="graph-path"),
    pytest.param("get", f"/v1/graph/sets/{SAMPLE_SET_ID}/traverse", None, id="graph-traverse"),
    pytest.param("get", "/v1/graph/residency-tree", None, id="graph-residency-tree"),
    pytest.param("post", "/v1/parser/tokenize", SAMPLE_BODY, id="parser-tokenize"),
    pytest.param("post", "/v1/parser/parse", SAMPLE_BODY, id="parser-parse"),
    pytest.param("post", "/v1/parser/compile", SAMPLE_BODY, id="parser-compile"),
    pytest.param("post", "/v1/pipeline/run", {"stages": ["normalize"], "payload": {}}, id="pipeline-run"),
    pytest.param("get", "/v1/concurrency/batch-score", None, id="concurrency-batch-score-get"),
    pytest.param("post", "/v1/concurrency/batch-score", {"ids": [SAMPLE_SET_ID]}, id="concurrency-batch-score-post"),
    pytest.param("get", "/v1/concurrency/ingest", None, id="concurrency-ingest-get"),
    pytest.param("post", "/v1/concurrency/ingest", {"source": "snapshot"}, id="concurrency-ingest-post"),
    pytest.param("get", "/v1/queue/jobs", None, id="queue-jobs"),
    pytest.param("get", "/v1/schedule", None, id="queue-schedule"),
    pytest.param("get", "/v1/queue/dead-letter", None, id="queue-dead-letter"),
    pytest.param("post", "/v1/queue/replay", {"job_id": "job-001"}, id="queue-replay"),
    pytest.param("post", "/v1/ingest/snapshot", {"snapshot": {"items": []}}, id="ingest-snapshot"),
    pytest.param("get", "/v1/rules/report", None, id="rules-report"),
    pytest.param("post", "/v1/sync/reconcile", {"remote": {"version": 1}}, id="sync-reconcile"),
    pytest.param(
        "post",
        "/v1/rebalance/route",
        {"source": "a", "target": "b", "graph": {}},
        id="rebalance-route",
    ),
    pytest.param("get", f"/v1/ai/recommend?set_id={SAMPLE_SET_ID}", None, id="ai-recommend-get"),
    pytest.param("post", "/v1/ai/recommend", {"set_id": SAMPLE_SET_ID}, id="ai-recommend-post"),
    pytest.param("get", f"/v1/ai/similar?set_id={SAMPLE_SET_ID}", None, id="ai-similar-get"),
    pytest.param("post", "/v1/ai/similar", {"set_id": SAMPLE_SET_ID}, id="ai-similar-post"),
]


@pytest.mark.parametrize("method,path,body", ROUTE_CASES)
@pytest.mark.django_db
def test_route_smoke(api_client, method, path, body):
    if method == "get":
        response = api_client.get(path)
    else:
        response = api_client.post(path, body, format="json")

    assert response.status_code == 200
    payload = response.json()
    assert "data" in payload


@pytest.mark.django_db
def test_response_envelope_helper():
    from common.responses import envelope

    response = envelope({"ok": True})
    assert response.status_code == 200
    assert response.data == {"data": {"ok": True}}


def test_service_container_mock_wiring(mock_service_container):
    assert mock_service_container.catalog.list_exhibitions() == []
    assert mock_service_container.worker.batch_score([])["scores"] == []
