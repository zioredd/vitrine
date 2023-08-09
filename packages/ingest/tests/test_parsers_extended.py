"""Extended parser tests."""

from __future__ import annotations

import pytest

from vitrine_ingest.normalizers import (
    batch_normalize,
    normalize_artist,
    normalize_iso_date,
    normalize_list_field,
    normalize_telemetry_record,
    normalize_url,
)
from vitrine_ingest.parsers import (
    auto_parse,
    detect_csv_dialect,
    parse_csv_with_dialect,
    parse_json_lines,
    parse_yamlish_kv,
)
from vitrine_ingest.reconcile import ReconcileStrategy, reconcile_with_strategy
from vitrine_ingest.snapshots import SnapshotBuilder, diff_snapshots


def test_detect_csv_dialect_comma():
    info = detect_csv_dialect("id,title\n1,Show")
    assert info.delimiter == ","
    assert info.has_header


def test_parse_csv_with_dialect():
    rows, info = parse_csv_with_dialect("id,title\nex-1,Test Show\n")
    assert len(rows) == 1
    assert rows[0]["title"] == "Test Show"


def test_parse_json_lines():
    text = '{"id": "1"}\n{"id": "2"}\n'
    records = parse_json_lines(text)
    assert len(records) == 2


def test_parse_json_lines_invalid():
    with pytest.raises(ValueError):
        parse_json_lines('{"bad"\n')


def test_parse_yamlish_kv():
    text = "---\nid: ex-1\ntitle: Show\n\n---\nid: ex-2\ntitle: Other\n"
    records = parse_yamlish_kv(text)
    assert len(records) == 2
    assert records[0]["id"] == "ex-1"


def test_auto_parse_json_array():
    records = auto_parse('[{"id": "1"}, {"id": "2"}]')
    assert len(records) == 2


def test_auto_parse_csv():
    records = auto_parse("id,name\n1,Alpha")
    assert records[0]["name"] == "Alpha"


def test_normalize_artist():
    assert normalize_artist("  van gogh  ") == "Van Gogh"


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com").startswith("https://")


def test_normalize_iso_date():
    assert normalize_iso_date("2026-01-15").year == 2026


def test_normalize_list_field():
    assert normalize_list_field("a, b, c") == ["a", "b", "c"]


def test_normalize_telemetry_record_clamps():
    rec = normalize_telemetry_record({"intensity": 2.0, "dwell_sec": -5})
    assert rec["intensity"] == 1.0
    assert rec["dwell_sec"] == 0.0


def test_batch_normalize():
    out = batch_normalize([{"intensity": 0.5}, {"intensity": 1.5}])
    assert len(out) == 2


def test_reconcile_with_strategy_merge():
    local = {"a": {"score": 10, "title": "Old"}}
    remote = {"a": {"score": 20, "genre": "jazz"}}
    result = reconcile_with_strategy(local, remote, ReconcileStrategy.MERGE_SHALLOW)
    assert "a" in result.merged
    assert result.merged["a"]["genre"] == "jazz"


def test_snapshot_builder_and_diff():
    builder_a = SnapshotBuilder("ex-1")
    builder_a.add_record({"id": "r1"})
    snap_a = builder_a.build("snap-a")
    builder_b = SnapshotBuilder("ex-1")
    builder_b.add_record({"id": "r1"})
    builder_b.add_record({"id": "r2"})
    snap_b = builder_b.build("snap-b")
    diff = diff_snapshots(snap_a, snap_b)
    assert "r2" in diff["added"]
