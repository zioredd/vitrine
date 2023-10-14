"""Integration tests against real seed data via create_service_container()."""

from __future__ import annotations

import pytest

from services.container import get_container

SAMPLE_SET_ID = "ex-000"


@pytest.mark.django_db
def test_seed_exhibition_count():
    container = get_container()
    exhibitions = container.catalog.list_exhibitions()
    assert len(exhibitions) == 48


@pytest.mark.django_db
def test_catalog_get_exhibition():
    container = get_container()
    detail = container.catalog.get_exhibition(SAMPLE_SET_ID)
    assert detail["id"] == SAMPLE_SET_ID
    assert detail.get("title")


@pytest.mark.django_db
def test_craft_pacing_returns_curve():
    container = get_container()
    data = container.mix.pacing(SAMPLE_SET_ID)
    assert data["set_id"] == SAMPLE_SET_ID
    assert "curve" in data
    assert len(data["curve"]) > 0
    assert "intensity" in data["curve"][0]


@pytest.mark.django_db
def test_craft_dialogue():
    container = get_container()
    data = container.mix.dialogue(SAMPLE_SET_ID)
    assert "wall_text_score" in data


@pytest.mark.django_db
def test_graph_path_on_real_exhibition():
    container = get_container()
    exhibition = container.catalog.get_exhibition(SAMPLE_SET_ID)
    nodes = exhibition.get("graph_nodes") or []
    if len(nodes) >= 2:
        target = nodes[-1]["id"]
        result = container.graph.shortest_path(SAMPLE_SET_ID, target)
        assert "path" in result
        assert isinstance(result["path"], list)


@pytest.mark.django_db
def test_graph_traverse():
    container = get_container()
    result = container.graph.traverse(SAMPLE_SET_ID, depth=5)
    assert "visited" in result


@pytest.mark.django_db
def test_graph_residency_tree():
    container = get_container()
    tree = container.graph.residency_tree()
    assert tree is not None


@pytest.mark.django_db
def test_rules_report_severity_counts():
    container = get_container()
    report = container.rules.run_report()
    assert "severity_counts" in report
    assert "violations" in report
    assert isinstance(report["severity_counts"], dict)


@pytest.mark.django_db
def test_intelligence_report():
    container = get_container()
    report = container.intelligence.report()
    assert report["exhibition_count"] == 48
    assert "avg_vitrine_score" in report


@pytest.mark.django_db
def test_command_center():
    container = get_container()
    data = container.intelligence.command_center()
    assert "active_exhibitions" in data
    assert data["active_exhibitions"] == 48


@pytest.mark.django_db
def test_enterprise_board_pack():
    container = get_container()
    pack = container.enterprise.board_pack()
    assert "executive_summary" in pack
    assert "kpis" in pack


@pytest.mark.django_db
def test_enterprise_program():
    container = get_container()
    programs = container.enterprise.program()
    assert isinstance(programs, list)
    assert len(programs) >= 1


@pytest.mark.django_db
def test_enterprise_compliance():
    container = get_container()
    compliance = container.enterprise.compliance()
    assert "checks" in compliance


@pytest.mark.django_db
def test_crowd_arc():
    container = get_container()
    arc = container.crowd.arc(SAMPLE_SET_ID)
    assert "completeness" in arc


@pytest.mark.django_db
def test_crowd_web():
    container = get_container()
    web = container.crowd.web(SAMPLE_SET_ID)
    assert "nodes" in web
    assert len(web["nodes"]) > 0


@pytest.mark.django_db
def test_crowd_theme_clusters():
    container = get_container()
    clusters = container.crowd.theme_clusters()
    assert isinstance(clusters, list)


@pytest.mark.django_db
def test_ai_similar():
    container = get_container()
    result = container.ai.similar(SAMPLE_SET_ID)
    assert "items" in result


@pytest.mark.django_db
def test_ai_recommend():
    container = get_container()
    result = container.ai.recommend(SAMPLE_SET_ID)
    assert "recommendations" in result


@pytest.mark.django_db
def test_ingest_snapshot():
    container = get_container()
    result = container.ingest.ingest_snapshot({"items": [{"id": "new-1", "title": "Import Test"}]})
    assert "imported" in result


@pytest.mark.django_db
def test_catalog_tags_and_format():
    container = get_container()
    tags = container.catalog.list_tags()
    spectrum = container.catalog.format_spectrum()
    assert isinstance(tags, list)
    assert isinstance(spectrum, list)


@pytest.mark.django_db
def test_editorial_risks():
    container = get_container()
    risks = container.editorial.risks()
    assert isinstance(risks, list)


@pytest.mark.django_db
def test_worker_batch_score():
    container = get_container()
    result = container.worker.batch_score(None)
    assert len(result["scores"]) == 48
