"""Pydantic domain models for the Vitrine curation platform."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, field_validator


class SignalKind(str, Enum):
    REVIEW = "review"
    VISITOR = "visitor"
    CRITIC = "critic"
    SOCIAL = "social"
    SALES = "sales"
    CURATOR = "curator"


class Severity(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"


class Provenance(BaseModel):
    source_name: str
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    captured_at: datetime | None = None
    rank: int | None = Field(default=None, ge=1)

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class Tag(BaseModel):
    id: str
    label: str
    category: str | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class Artwork(BaseModel):
    id: str
    title: str
    artist: str
    medium: str | None = None
    year: int | None = None
    dwell_sec: float = Field(default=0.0, ge=0.0)
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    narrative_tension: float = Field(default=0.5, ge=0.0, le=1.0)
    wall_text_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    position: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)


class Room(BaseModel):
    id: str
    name: str
    floor: int = 0
    capacity: int = Field(default=50, ge=1)
    artworks: list[Artwork] = Field(default_factory=list)


class Signal(BaseModel):
    id: str
    exhibition_id: str
    kind: SignalKind
    score: float = Field(ge=0.0, le=100.0)
    text: str | None = None
    provenance: Provenance
    weight: float = Field(default=1.0, ge=0.0)


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str = "artwork"
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source_id: str
    target_id: str
    weight: float = Field(default=1.0, ge=0.0)
    relation: str = "adjacent"


class VenueMetadata(BaseModel):
    name: str
    city: str | None = None
    country: str | None = None
    format: str | None = None
    capacity: int | None = None


class Exhibition(BaseModel):
    id: str
    title: str
    curator: str
    imprint: str | None = None
    genre: str | None = None
    series: str | None = None
    residency: str | None = None
    opened_on: date | None = None
    closed_on: date | None = None
    rooms: list[Room] = Field(default_factory=list)
    signals: list[Signal] = Field(default_factory=list)
    graph_nodes: list[GraphNode] = Field(default_factory=list)
    graph_edges: list[GraphEdge] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    venue: VenueMetadata | None = None
    crowd_score: float | None = Field(default=None, ge=0.0, le=100.0)
    vitrine_score: float | None = Field(default=None, ge=0.0, le=100.0)

    def all_artworks(self) -> list[Artwork]:
        return [art for room in self.rooms for art in room.artworks]


class Snapshot(BaseModel):
    id: str
    exhibition_id: str
    captured_at: datetime
    payload: dict[str, Any]
    checksum: str | None = None


class Job(BaseModel):
    id: str
    name: str
    status: JobStatus = JobStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)
    payload: dict[str, Any] = Field(default_factory=dict)
    attempts: int = 0
    max_attempts: int = 3
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
