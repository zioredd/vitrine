"""Transition scoring matrix for artwork sequencing."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from vitrine_types.models import Artwork, Exhibition


@dataclass
class TransitionCell:
    from_id: str
    to_id: str
    intensity_delta: float
    tension_delta: float
    score: float
    label: str


@dataclass
class TransitionMatrix:
    artwork_ids: list[str]
    cells: list[TransitionCell]
    avg_score: float
    min_score: float
    max_score: float
    size: int = 0


@dataclass
class PathScore:
    artwork_ids: list[str]
    total_score: float
    avg_transition: float
    weak_links: list[tuple[str, str]] = field(default_factory=list)


def _transition_score(
    from_art: Artwork,
    to_art: Artwork,
    *,
    max_intensity_delta: float = 0.35,
    max_tension_delta: float = 0.4,
) -> tuple[float, str]:
    i_delta = abs(to_art.intensity - from_art.intensity)
    t_delta = abs(to_art.narrative_tension - from_art.narrative_tension)

    i_score = max(0.0, 1.0 - i_delta / max_intensity_delta) if max_intensity_delta else 0.0
    t_score = max(0.0, 1.0 - t_delta / max_tension_delta) if max_tension_delta else 0.0

    tag_overlap = len(set(from_art.tags) & set(to_art.tags))
    tag_bonus = min(0.15, tag_overlap * 0.05)

    score = 0.55 * i_score + 0.35 * t_score + tag_bonus

    if i_delta <= 0.15 and t_delta <= 0.2:
        label = "smooth"
    elif i_delta > 0.5 or t_delta > 0.5:
        label = "sharp"
    else:
        label = "moderate"

    return round(min(1.0, score), 3), label


def build_transition_matrix(exhibition: Exhibition) -> TransitionMatrix:
    """Build full pairwise transition matrix for ordered artworks."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    ids = [a.id for a in arts]
    cells: list[TransitionCell] = []

    for i, from_art in enumerate(arts):
        for j, to_art in enumerate(arts):
            if i == j:
                continue
            score, label = _transition_score(from_art, to_art)
            cells.append(
                TransitionCell(
                    from_id=from_art.id,
                    to_id=to_art.id,
                    intensity_delta=round(abs(to_art.intensity - from_art.intensity), 3),
                    tension_delta=round(abs(to_art.narrative_tension - from_art.narrative_tension), 3),
                    score=score,
                    label=label,
                )
            )

    scores = [c.score for c in cells] if cells else [0.0]
    return TransitionMatrix(
        artwork_ids=ids,
        cells=cells,
        avg_score=round(sum(scores) / len(scores), 3),
        min_score=round(min(scores), 3),
        max_score=round(max(scores), 3),
        size=len(arts),
    )


def sequential_transitions(exhibition: Exhibition) -> list[TransitionCell]:
    """Score only consecutive artwork transitions in display order."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    cells: list[TransitionCell] = []
    for i in range(len(arts) - 1):
        a, b = arts[i], arts[i + 1]
        score, label = _transition_score(a, b)
        cells.append(
            TransitionCell(
                from_id=a.id,
                to_id=b.id,
                intensity_delta=round(abs(b.intensity - a.intensity), 3),
                tension_delta=round(abs(b.narrative_tension - a.narrative_tension), 3),
                score=score,
                label=label,
            )
        )
    return cells


def score_path(artworks: list[Artwork]) -> PathScore:
    """Score a specific artwork ordering path."""
    if len(artworks) < 2:
        return PathScore(artwork_ids=[a.id for a in artworks], total_score=1.0, avg_transition=1.0)

    transitions: list[TransitionCell] = []
    for i in range(len(artworks) - 1):
        score, label = _transition_score(artworks[i], artworks[i + 1])
        transitions.append(
            TransitionCell(
                from_id=artworks[i].id,
                to_id=artworks[i + 1].id,
                intensity_delta=round(abs(artworks[i + 1].intensity - artworks[i].intensity), 3),
                tension_delta=round(abs(artworks[i + 1].narrative_tension - artworks[i].narrative_tension), 3),
                score=score,
                label=label,
            )
        )

    scores = [t.score for t in transitions]
    weak = [(t.from_id, t.to_id) for t in transitions if t.score < 0.4]

    return PathScore(
        artwork_ids=[a.id for a in artworks],
        total_score=round(sum(scores), 3),
        avg_transition=round(sum(scores) / len(scores), 3),
        weak_links=weak,
    )


def optimal_reorder_greedy(exhibition: Exhibition) -> list[str]:
    """Greedy nearest-neighbor reorder by transition score."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    if len(arts) <= 2:
        return [a.id for a in arts]

    remaining = list(arts)
    path = [remaining.pop(0)]
    while remaining:
        current = path[-1]
        cur_art = next(a for a in arts if a.id == current.id)
        best_idx = 0
        best_score = -1.0
        for idx, candidate in enumerate(remaining):
            score, _ = _transition_score(cur_art, candidate)
            if score > best_score:
                best_score = score
                best_idx = idx
        path.append(remaining.pop(best_idx))
    return [a.id for a in path]


def matrix_heatmap_data(matrix: TransitionMatrix) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for from_id in matrix.artwork_ids:
        row: dict[str, object] = {"from": from_id}
        for to_id in matrix.artwork_ids:
            cell = next((c for c in matrix.cells if c.from_id == from_id and c.to_id == to_id), None)
            row[to_id] = cell.score if cell else None
        rows.append(row)
    return rows


def transition_entropy(exhibition: Exhibition) -> float:
    """Shannon entropy of sequential transition scores ( diversity measure )."""
    cells = sequential_transitions(exhibition)
    if not cells:
        return 0.0
    scores = [c.score for c in cells]
    total = sum(scores)
    if total <= 0:
        return 0.0
    probs = [s / total for s in scores]
    return round(-sum(p * math.log2(p) for p in probs if p > 0), 3)
