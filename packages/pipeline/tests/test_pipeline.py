from vitrine_pipeline.runner import StageRunner, snapshot_diff


def test_stage_runner_decode_normalize():
    runner = StageRunner()
    ctx = runner.run({"raw_records": [{"id": "1", "title": "Show"}], "required": ["id", "title"]})
    assert "decode" in ctx.stages_run
    assert "normalize" in ctx.stages_run
    assert len(ctx.data["normalized"]) == 1


def test_snapshot_diff_added():
    diff = snapshot_diff({"a": 1}, {"a": 1, "b": 2})
    assert diff["added"] == {"b": 2}


def test_snapshot_diff_removed():
    diff = snapshot_diff({"a": 1, "b": 2}, {"a": 1})
    assert diff["removed"] == {"b": 2}


def test_snapshot_diff_changed():
    diff = snapshot_diff({"score": 80}, {"score": 90})
    assert "score" in diff["changed"]


def test_snapshot_diff_no_changes():
    diff = snapshot_diff({"x": 1}, {"x": 1})
    assert diff["added"] == {}
    assert diff["changed"] == {}


def test_pipeline_validation_errors():
    runner = StageRunner()
    ctx = runner.run({"raw_records": [{"id": ""}], "required": ["id", "title"]})
    assert ctx.data.get("validation_errors")
