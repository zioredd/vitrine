"""Catalog repository over seed data with graceful fallback."""

from __future__ import annotations

from dataclasses import dataclass, field

from vitrine_types.models import Exhibition

try:
    from vitrine_catalog.seed_profiles import SEED_EXHIBITIONS
except ImportError:
    SEED_EXHIBITIONS: list[Exhibition] = []


@dataclass
class CatalogFilter:
    residency: str | None = None
    series: str | None = None
    genre: str | None = None
    min_score: float | None = None
    curator: str | None = None


@dataclass
class CatalogRepository:
    """In-memory repository backed by seed exhibitions.

    Use ``CatalogRepository()`` for an empty in-memory store, or
    ``CatalogRepository.from_seed()`` to load the generated seed corpus.
    When constructed with no exhibitions, seed data is loaded automatically
    if ``SEED_EXHIBITIONS`` is available.
    """

    _exhibitions: list[Exhibition] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self._exhibitions and SEED_EXHIBITIONS:
            self._exhibitions = list(SEED_EXHIBITIONS)

    @classmethod
    def from_seed(cls) -> "CatalogRepository":
        """Explicitly load exhibitions from ``seed_profiles.SEED_EXHIBITIONS``."""
        return cls(_exhibitions=list(SEED_EXHIBITIONS))

    @classmethod
    def from_list(cls, exhibitions: list[Exhibition]) -> "CatalogRepository":
        return cls(_exhibitions=list(exhibitions))

    def load_all(self) -> list[Exhibition]:
        return list(self._exhibitions)

    def get_by_id(self, exhibition_id: str) -> Exhibition | None:
        for ex in self._exhibitions:
            if ex.id == exhibition_id:
                return ex
        return None

    def filter(self, criteria: CatalogFilter) -> list[Exhibition]:
        results: list[Exhibition] = []
        for ex in self._exhibitions:
            if criteria.residency and ex.residency != criteria.residency:
                continue
            if criteria.series and ex.series != criteria.series:
                continue
            if criteria.genre and ex.genre != criteria.genre:
                continue
            if criteria.curator and ex.curator != criteria.curator:
                continue
            if criteria.min_score is not None:
                score = ex.vitrine_score or 0.0
                if score < criteria.min_score:
                    continue
            results.append(ex)
        return results

    def count_artworks(self) -> int:
        return sum(len(ex.all_artworks()) for ex in self._exhibitions)

    def upsert(self, exhibition: Exhibition) -> None:
        for i, ex in enumerate(self._exhibitions):
            if ex.id == exhibition.id:
                self._exhibitions[i] = exhibition
                return
        self._exhibitions.append(exhibition)

    def delete(self, exhibition_id: str) -> bool:
        before = len(self._exhibitions)
        self._exhibitions = [e for e in self._exhibitions if e.id != exhibition_id]
        return len(self._exhibitions) < before
