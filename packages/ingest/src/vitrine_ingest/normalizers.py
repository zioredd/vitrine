"""Extended field normalizers for ingest pipeline."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse


def normalize_unicode(value: str) -> str:
    return unicodedata.normalize("NFKC", value.strip())


def normalize_artist(value: str) -> str:
    cleaned = normalize_unicode(value)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.title()


def normalize_medium(value: str) -> str:
    return normalize_unicode(value).lower()


def normalize_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value if "://" in value else f"https://{value}")
    if not parsed.netloc:
        return None
    return parsed.geturl()


def normalize_iso_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def normalize_list_field(value: Any, sep: str = ",") -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [p.strip() for p in value.split(sep) if p.strip()]
    return []


def normalize_telemetry_record(record: dict[str, Any]) -> dict[str, Any]:
    out = dict(record)
    for key in ("intensity", "narrative_tension", "wall_text_ratio"):
        if key in out:
            out[key] = max(0.0, min(1.0, float(out[key])))
    if "dwell_sec" in out:
        out["dwell_sec"] = max(0.0, float(out["dwell_sec"]))
    if "artist" in out and isinstance(out["artist"], str):
        out["artist"] = normalize_artist(out["artist"])
    if "source_url" in out and isinstance(out["source_url"], str):
        out["source_url"] = normalize_url(out["source_url"])
    return out


def batch_normalize(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_telemetry_record(r) for r in records]
