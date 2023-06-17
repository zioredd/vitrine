"""Provenance audit trails with lineage tracking and confidence decay."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from vitrine_types.models import Exhibition, Signal


@dataclass
class TrailEntry:
    signal_id: str
    exhibition_id: str
    source_name: str
    confidence: float
    captured_at: datetime | None
    rank: int | None
    score: float
    chain_depth: int


@dataclass
class ProvenanceTrail:
    exhibition_id: str
    entries: list[TrailEntry]
    avg_confidence: float
    weakest_link: TrailEntry | None
    source_diversity: int

    @property
    def is_complete(self) -> bool:
        return all(e.confidence >= 0.5 for e in self.entries) and self.source_diversity >= 2


@dataclass
class AuditTrailReport:
    trails: list[ProvenanceTrail]
    total_signals: int
    incomplete_count: int
    confidence_histogram: dict[str, int]
    stale_signals: list[str] = field(default_factory=list)


def build_provenance_trail(exhibition: Exhibition) -> ProvenanceTrail:
    """Construct ordered provenance trail for one exhibition."""
    sorted_signals = sorted(
        exhibition.signals,
        key=lambda s: (s.provenance.rank or 999, -(s.provenance.confidence)),
    )
    entries: list[TrailEntry] = []
    for depth, sig in enumerate(sorted_signals):
        entries.append(
            TrailEntry(
                signal_id=sig.id,
                exhibition_id=exhibition.id,
                source_name=sig.provenance.source_name,
                confidence=sig.provenance.confidence,
                captured_at=sig.provenance.captured_at,
                rank=sig.provenance.rank,
                score=sig.score,
                chain_depth=depth,
            )
        )

    avg = sum(e.confidence for e in entries) / len(entries) if entries else 0.0
    weakest = min(entries, key=lambda e: e.confidence) if entries else None
    sources = {e.source_name for e in entries}
    return ProvenanceTrail(
        exhibition_id=exhibition.id,
        entries=entries,
        avg_confidence=round(avg, 3),
        weakest_link=weakest,
        source_diversity=len(sources),
    )


def audit_trails(
    exhibitions: list[Exhibition],
    stale_days: int = 365,
    reference: date | None = None,
) -> AuditTrailReport:
    """Build audit trails across catalog with staleness detection."""
    reference = reference or date.today()
    trails = [build_provenance_trail(ex) for ex in exhibitions]
    total = sum(len(t.entries) for t in trails)
    incomplete = sum(1 for t in trails if not t.is_complete)

    histogram = {"0.0-0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-1.0": 0}
    stale: list[str] = []
    for trail in trails:
        for entry in trail.entries:
            if entry.confidence < 0.3:
                histogram["0.0-0.3"] += 1
            elif entry.confidence < 0.5:
                histogram["0.3-0.5"] += 1
            elif entry.confidence < 0.7:
                histogram["0.5-0.7"] += 1
            else:
                histogram["0.7-1.0"] += 1
            if entry.captured_at:
                age = (reference - entry.captured_at.date()).days
                if age > stale_days:
                    stale.append(entry.signal_id)

    return AuditTrailReport(
        trails=trails,
        total_signals=total,
        incomplete_count=incomplete,
        confidence_histogram=histogram,
        stale_signals=stale,
    )


def merge_trails(primary: ProvenanceTrail, secondary: ProvenanceTrail) -> ProvenanceTrail:
    """Merge two trails preferring higher-confidence entries per source."""
    by_source: dict[str, TrailEntry] = {}
    for entry in primary.entries + secondary.entries:
        existing = by_source.get(entry.source_name)
        if existing is None or entry.confidence > existing.confidence:
            by_source[entry.source_name] = entry
    merged = sorted(by_source.values(), key=lambda e: e.chain_depth)
    avg = sum(e.confidence for e in merged) / len(merged) if merged else 0.0
    return ProvenanceTrail(
        exhibition_id=primary.exhibition_id,
        entries=merged,
        avg_confidence=round(avg, 3),
        weakest_link=min(merged, key=lambda e: e.confidence) if merged else None,
        source_diversity=len(by_source),
    )


def signal_lineage_score(signal: Signal, ancestors: list[Signal]) -> float:
    """Score how well a signal fits its provenance lineage."""
    if not ancestors:
        return signal.provenance.confidence
    ancestor_conf = sum(a.provenance.confidence for a in ancestors) / len(ancestors)
    score_delta = abs(signal.score - sum(a.score for a in ancestors) / len(ancestors))
    consistency = max(0.0, 1.0 - score_delta / 100.0)
    return round(signal.provenance.confidence * 0.6 + ancestor_conf * 0.2 + consistency * 0.2, 3)
