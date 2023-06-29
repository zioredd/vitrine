"""Transition matrix builder for mix analytics."""

from __future__ import annotations

from dataclasses import dataclass, field

from vitrine_types.models import Artwork, Exhibition


@dataclass
class MatrixEntry:
    row: int
    col: int
    from_id: str
    to_id: str
    intensity_delta: float
    dwell_delta: float
    weight: float


@dataclass
class MixTransitionMatrix:
    labels: list[str]
    size: int
    entries: list[MatrixEntry]
    row_sums: list[float]
    col_sums: list[float]
    stationary_hint: list[float] = field(default_factory=list)


def _artwork_deltas(a: Artwork, b: Artwork) -> tuple[float, float, float]:
    i_delta = abs(b.intensity - a.intensity)
    d_delta = abs(b.dwell_sec - a.dwell_sec)
    weight = max(0.05, 1.0 - i_delta)
    return i_delta, d_delta, weight


def build_mix_transition_matrix(
    exhibition: Exhibition,
    *,
    normalized: bool = True,
) -> MixTransitionMatrix:
    """Build row-stochastic transition matrix from artwork sequence."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    labels = [a.id for a in arts]
    n = len(arts)
    entries: list[MatrixEntry] = []
    raw_rows: list[list[float]] = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            i_delta, d_delta, weight = _artwork_deltas(arts[i], arts[j])
            raw_rows[i][j] = weight
            entries.append(
                MatrixEntry(
                    row=i,
                    col=j,
                    from_id=arts[i].id,
                    to_id=arts[j].id,
                    intensity_delta=round(i_delta, 3),
                    dwell_delta=round(d_delta, 3),
                    weight=round(weight, 3),
                )
            )

    row_sums: list[float] = []
    for i in range(n):
        row_sum = sum(raw_rows[i])
        if normalized and row_sum > 0:
            for j in range(n):
                raw_rows[i][j] /= row_sum
        row_sums.append(round(row_sum, 3) if not normalized else 1.0 if row_sum > 0 else 0.0)

    col_sums = [round(sum(raw_rows[i][j] for i in range(n)), 3) for j in range(n)]
    stationary = _power_iteration(raw_rows) if n > 0 else []

    for entry in entries:
        entry.weight = round(raw_rows[entry.row][entry.col], 3)

    return MixTransitionMatrix(
        labels=labels,
        size=n,
        entries=entries,
        row_sums=row_sums,
        col_sums=col_sums,
        stationary_hint=[round(s, 4) for s in stationary],
    )


def _power_iteration(matrix: list[list[float]], iterations: int = 20) -> list[float]:
    n = len(matrix)
    if n == 0:
        return []
    vec = [1.0 / n] * n
    for _ in range(iterations):
        new_vec = [0.0] * n
        for j in range(n):
            for i in range(n):
                new_vec[j] += vec[i] * matrix[i][j]
        total = sum(new_vec)
        if total > 0:
            vec = [v / total for v in new_vec]
    return vec


def sequential_matrix(exhibition: Exhibition) -> MixTransitionMatrix:
    """Build matrix where only consecutive transitions are allowed."""
    arts = sorted(exhibition.all_artworks(), key=lambda a: a.position)
    labels = [a.id for a in arts]
    n = len(arts)
    entries: list[MatrixEntry] = []
    raw_rows = [[0.0] * n for _ in range(n)]

    for i in range(n - 1):
        i_delta, d_delta, weight = _artwork_deltas(arts[i], arts[i + 1])
        raw_rows[i][i + 1] = 1.0
        entries.append(
            MatrixEntry(
                row=i,
                col=i + 1,
                from_id=arts[i].id,
                to_id=arts[i + 1].id,
                intensity_delta=round(i_delta, 3),
                dwell_delta=round(d_delta, 3),
                weight=1.0,
            )
        )

    row_sums = [sum(raw_rows[i]) for i in range(n)]
    col_sums = [sum(raw_rows[i][j] for i in range(n)) for j in range(n)]

    return MixTransitionMatrix(
        labels=labels,
        size=n,
        entries=entries,
        row_sums=row_sums,
        col_sums=col_sums,
        stationary_hint=[],
    )


def matrix_to_nested_list(matrix: MixTransitionMatrix) -> list[list[float]]:
    n = matrix.size
    grid = [[0.0] * n for _ in range(n)]
    for entry in matrix.entries:
        grid[entry.row][entry.col] = entry.weight
    return grid


def high_transition_pairs(matrix: MixTransitionMatrix, threshold: float = 0.7) -> list[tuple[str, str, float]]:
    return [
        (e.from_id, e.to_id, e.weight)
        for e in matrix.entries
        if e.weight >= threshold
    ]


def matrix_entropy(matrix: MixTransitionMatrix) -> float:
    import math

    entropy = 0.0
    for entry in matrix.entries:
        if entry.weight > 0:
            entropy -= entry.weight * math.log2(entry.weight)
    return round(entropy, 3)
