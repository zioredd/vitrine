"""Heuristic recommender for transitions and similar exhibitions."""

from __future__ import annotations

from dataclasses import dataclass

from vitrine_catalog.repository import CatalogRepository
from vitrine_mix.craft import transition_density
from vitrine_types.models import Artwork, Exhibition


@dataclass
class TransitionSuggestion:
    from_artwork_id: str
    to_artwork_id: str
    score: float
    reason: str


@dataclass
class ExhibitionMatch:
    exhibition_id: str
    title: str
    similarity: float
    shared_genre: bool


def suggest_transitions(exhibition: Exhibition, max_delta: float = 0.35) -> list[TransitionSuggestion]:
    """Recommend artwork order transitions with moderate intensity change."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    suggestions: list[TransitionSuggestion] = []
    for i in range(len(arts) - 1):
        a, b = arts[i], arts[i + 1]
        delta = abs(b.intensity - a.intensity)
        if delta <= max_delta:
            score = 1.0 - delta / max_delta
            suggestions.append(
                TransitionSuggestion(
                    from_artwork_id=a.id,
                    to_artwork_id=b.id,
                    score=round(score, 3),
                    reason=f"smooth delta {delta:.2f}",
                )
            )
        else:
            suggestions.append(
                TransitionSuggestion(
                    from_artwork_id=a.id,
                    to_artwork_id=b.id,
                    score=round(max(0.0, 0.5 - delta), 3),
                    reason=f"sharp delta {delta:.2f} — consider buffer piece",
                )
            )
    return sorted(suggestions, key=lambda s: -s.score)


def exhibition_similarity(a: Exhibition, b: Exhibition) -> float:
    """Heuristic similarity from genre, curator, tag overlap, and score proximity."""
    score = 0.0
    if a.genre and b.genre and a.genre == b.genre:
        score += 0.3
    if a.curator == b.curator:
        score += 0.15
    tags_a = {t.label for t in a.tags}
    tags_b = {t.label for t in b.tags}
    if tags_a and tags_b:
        overlap = len(tags_a & tags_b) / len(tags_a | tags_b)
        score += 0.25 * overlap
    sa = a.vitrine_score or 50.0
    sb = b.vitrine_score or 50.0
    score += 0.3 * max(0.0, 1.0 - abs(sa - sb) / 100.0)
    return round(min(1.0, score), 3)


def find_similar_exhibitions(
    target: Exhibition,
    catalog: CatalogRepository,
    limit: int = 5,
) -> list[ExhibitionMatch]:
    matches: list[ExhibitionMatch] = []
    for ex in catalog.load_all():
        if ex.id == target.id:
            continue
        sim = exhibition_similarity(target, ex)
        if sim > 0.1:
            matches.append(
                ExhibitionMatch(
                    exhibition_id=ex.id,
                    title=ex.title,
                    similarity=sim,
                    shared_genre=bool(target.genre and target.genre == ex.genre),
                )
            )
    return sorted(matches, key=lambda m: -m.similarity)[:limit]


def recommend_pacing_adjustments(exhibition: Exhibition) -> list[str]:
    """Heuristic pacing recommendations based on transition density."""
    trans = transition_density(exhibition.all_artworks())
    recs: list[str] = []
    if trans.density > 0.8:
        recs.append("High transition volatility — insert lower-intensity buffer works")
    if trans.density < 0.2:
        recs.append("Flat pacing — add intensity peaks in middle third")
    if trans.max_delta > 0.6:
        recs.append(f"Max intensity jump {trans.max_delta:.2f} exceeds comfort threshold")
    if not recs:
        recs.append("Pacing profile within recommended bounds")
    return recs
