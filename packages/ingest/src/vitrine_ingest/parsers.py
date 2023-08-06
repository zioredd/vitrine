"""Extended parsers: CSV dialect detection, JSON Lines, YAML-ish KV."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class CsvDialectInfo:
    delimiter: str
    quotechar: str
    has_header: bool
    confidence: float


def detect_csv_dialect(text: str, sample_lines: int = 5) -> CsvDialectInfo:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()][:sample_lines]
    if not lines:
        return CsvDialectInfo(",", '"', True, 0.0)
    candidates = [(",", '"'), (";", '"'), ("\t", '"'), ("|", '"')]
    best = candidates[0]
    best_score = -1.0
    for delim, quote in candidates:
        counts = [line.count(delim) for line in lines]
        if not counts or min(counts) == 0:
            continue
        variance = max(counts) - min(counts)
        score = sum(counts) - variance
        if score > best_score:
            best_score = score
            best = (delim, quote)
    header_like = lines[0].replace(best[0], " ").split()
    has_header = not all(part.replace(".", "").isdigit() for part in header_like if part)
    confidence = min(1.0, best_score / max(1, len(lines)))
    return CsvDialectInfo(best[0], best[1], has_header, round(confidence, 3))


def parse_csv_with_dialect(text: str) -> tuple[list[dict[str, str]], CsvDialectInfo]:
    info = detect_csv_dialect(text)
    reader = csv.DictReader(
        io.StringIO(text.strip()),
        delimiter=info.delimiter,
        quotechar=info.quotechar,
    )
    return [dict(row) for row in reader], info


def parse_json_lines(text: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on line {line_no}") from exc
        if not isinstance(obj, dict):
            raise ValueError(f"line {line_no} must be a JSON object")
        records.append(obj)
    return records


def parse_yamlish_kv(text: str) -> list[dict[str, Any]]:
    """Parse indented key: value blocks (YAML-ish, not full YAML)."""
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    list_key: str | None = None
    for raw in text.splitlines():
        if not raw.strip():
            if current:
                records.append(current)
                current = None
                list_key = None
            continue
        if raw.startswith("---"):
            if current:
                records.append(current)
            current = {}
            list_key = None
            continue
        if current is None:
            current = {}
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()
        if stripped.startswith("- ") and list_key and current is not None:
            current.setdefault(list_key, [])
            if isinstance(current[list_key], list):
                current[list_key].append(stripped[2:].strip())
            continue
        if ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if not val and indent <= 2:
                list_key = key
                current[key] = []
            elif val.isdigit():
                current[key] = int(val)
            else:
                try:
                    current[key] = float(val)
                except ValueError:
                    current[key] = val.strip('"').strip("'")
    if current:
        records.append(current)
    return records


def auto_parse(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("[") or stripped.startswith("{"):
        data = json.loads(stripped)
        return data if isinstance(data, list) else [data]
    if "\n{" in stripped or stripped.startswith("{"):
        try:
            return parse_json_lines(stripped)
        except ValueError:
            pass
    if "---" in stripped or re.search(r"^\w+:\s*$", stripped, re.MULTILINE):
        return parse_yamlish_kv(stripped)
    rows, _ = parse_csv_with_dialect(stripped)
    return rows
