from datetime import date

from vitrine_ingest.pipeline import (
    dedupe_records,
    enrich_record,
    normalize_date,
    normalize_genre,
    normalize_score,
    parse_csv,
    parse_json_records,
    parse_line_kv,
    reconcile_records,
    run_ingest_pipeline,
    validate_record,
)


def test_parse_csv():
    rows = parse_csv("id,title\n1,Show\n2,Other")
    assert len(rows) == 2
    assert rows[0]["title"] == "Show"


def test_parse_json_array():
    rows = parse_json_records('[{"id":"1"},{"id":"2"}]')
    assert len(rows) == 2


def test_parse_line_kv():
    text = "id=1\ntitle=Show\n\nid=2\ntitle=Other"
    rows = parse_line_kv(text)
    assert len(rows) == 2


def test_normalize_date():
    assert normalize_date("2026-07-21") == date(2026, 7, 21)


def test_normalize_genre():
    assert normalize_genre("  Contemporary  Art ") == "contemporary art"


def test_normalize_score_clamps():
    assert normalize_score(150) == 100.0
    assert normalize_score(-5) == 0.0


def test_dedupe_records():
    records = [{"id": "1"}, {"id": "1"}, {"id": "2"}]
    out, dupes = dedupe_records(records)
    assert len(out) == 2
    assert dupes == 1


def test_enrich_record():
    rec = enrich_record({"genre": " MODERN ", "score": "85", "title": "  Hello  "})
    assert rec["genre"] == "modern"
    assert rec["_ingested"] is True


def test_validate_required():
    errs = validate_record({}, ["id", "title"])
    assert len(errs) == 2


def test_run_ingest_pipeline():
    raw = [{"id": "1", "title": "A", "score": 90}, {"id": "1", "title": "dup"}]
    result = run_ingest_pipeline(raw, required=["id", "title"])
    assert result.deduped == 1
    assert len(result.records) == 1


def test_reconcile_records():
    existing = {"1": {"id": "1", "score": 80}}
    incoming = [{"id": "1", "title": "Updated"}, {"id": "2", "title": "New"}]
    merged = reconcile_records(existing, incoming)
    assert merged["1"]["title"] == "Updated"
    assert "2" in merged
