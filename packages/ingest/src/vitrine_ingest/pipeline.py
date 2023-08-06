"""CSV/JSON/line KV parsers, normalizers, validators, reconcile pipeline."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable


def parse_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text.strip()))
    return [dict(row) for row in reader]


def parse_json_records(text: str) -> list[dict[str, Any]]:
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("JSON must be object or array")


def parse_line_kv(text: str, sep: str = "=") -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        if sep in line:
            key, val = line.split(sep, 1)
            current[key.strip()] = val.strip()
    if current:
        records.append(current)
    return records


# --- Normalizers ---

def normalize_date(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def normalize_genre(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_score(value: str | float) -> float:
    v = float(value)
    return max(0.0, min(100.0, v))


def normalize_rank(value: str | int) -> int:
    return max(1, int(value))


def normalize_confidence(value: str | float) -> float:
    v = float(value)
    return max(0.0, min(1.0, v))


def normalize_text(value: str, max_len: int = 500) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned[:max_len]


# --- Validators ---

@dataclass
class ValidationError:
    field: str
    message: str
    severity: str = "error"


def validate_record(record: dict[str, Any], required: list[str]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for field_name in required:
        if field_name not in record or record[field_name] in (None, ""):
            errors.append(ValidationError(field=field_name, message="required"))
    if "score" in record:
        try:
            s = float(record["score"])
            if not 0 <= s <= 100:
                errors.append(ValidationError(field="score", message="out of range"))
        except (TypeError, ValueError):
            errors.append(ValidationError(field="score", message="invalid number"))
    if "confidence" in record:
        try:
            c = float(record["confidence"])
            if not 0 <= c <= 1:
                errors.append(ValidationError(field="confidence", message="out of range"))
        except (TypeError, ValueError):
            errors.append(ValidationError(field="confidence", message="invalid"))
    return errors


@dataclass
class IngestResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    errors: list[ValidationError] = field(default_factory=list)
    deduped: int = 0


def dedupe_records(records: list[dict[str, Any]], key: str = "id") -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    dupes = 0
    for rec in records:
        k = str(rec.get(key, ""))
        if k in seen:
            dupes += 1
            continue
        seen.add(k)
        out.append(rec)
    return out, dupes


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    if "genre" in enriched and isinstance(enriched["genre"], str):
        enriched["genre"] = normalize_genre(enriched["genre"])
    if "score" in enriched:
        enriched["score"] = normalize_score(enriched["score"])
    if "confidence" in enriched:
        enriched["confidence"] = normalize_confidence(enriched["confidence"])
    if "title" in enriched and isinstance(enriched["title"], str):
        enriched["title"] = normalize_text(enriched["title"])
    enriched["_ingested"] = True
    return enriched


def reconcile_records(
    existing: dict[str, dict[str, Any]],
    incoming: list[dict[str, Any]],
    key: str = "id",
) -> dict[str, dict[str, Any]]:
    merged = dict(existing)
    for rec in incoming:
        k = str(rec[key])
        if k in merged:
            merged[k] = {**merged[k], **rec}
        else:
            merged[k] = rec
    return merged


def run_ingest_pipeline(
    raw_records: list[dict[str, Any]],
    required: list[str] | None = None,
    dedupe_key: str = "id",
) -> IngestResult:
    """dedupe -> enrich -> validate -> reconcile-ready output."""
    required = required or ["id"]
    deduped, dup_count = dedupe_records(raw_records, dedupe_key)
    enriched = [enrich_record(r) for r in deduped]
    result = IngestResult(deduped=dup_count)
    for rec in enriched:
        errs = validate_record(rec, required)
        if errs:
            result.errors.extend(errs)
        else:
            result.records.append(rec)
    return result
