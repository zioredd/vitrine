from vitrine_catalog.repository import CatalogRepository
from vitrine_types.models import Artwork, Exhibition, Room, Tag

from vitrine_ai.recommender import (
    exhibition_similarity,
    find_similar_exhibitions,
    recommend_pacing_adjustments,
    suggest_transitions,
)


def _ex(id_: str, **kwargs) -> Exhibition:
    defaults = {"title": id_, "curator": "C"}
    defaults.update(kwargs)
    return Exhibition(id=id_, **defaults)


def test_suggest_transitions_smooth():
    ex = Exhibition(
        id="ex",
        title="T",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A", artist="X", position=0, intensity=0.5),
                    Artwork(id="a2", title="B", artist="Y", position=1, intensity=0.6),
                ],
            )
        ],
    )
    suggestions = suggest_transitions(ex)
    assert len(suggestions) == 1
    assert suggestions[0].score > 0.5


def test_exhibition_similarity_same_genre():
    a = _ex("1", genre="modern", vitrine_score=80, tags=[Tag(id="t", label="light")])
    b = _ex("2", genre="modern", vitrine_score=75, tags=[Tag(id="t", label="light")])
    assert exhibition_similarity(a, b) >= 0.5


def test_find_similar_exhibitions():
    target = _ex("t", genre="modern", vitrine_score=80)
    others = [_ex("1", genre="modern", vitrine_score=78), _ex("2", genre="classical", vitrine_score=40)]
    catalog = CatalogRepository.from_list(others)
    matches = find_similar_exhibitions(target, catalog)
    assert matches[0].shared_genre


def test_recommend_pacing_flat():
    ex = Exhibition(
        id="ex",
        title="Flat",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id=f"a{i}", title=f"A{i}", artist="X", position=i, intensity=0.5)
                    for i in range(4)
                ],
            )
        ],
    )
    recs = recommend_pacing_adjustments(ex)
    assert any("Flat" in r or "bounds" in r for r in recs)


def test_sharp_transition_low_score():
    ex = Exhibition(
        id="ex",
        title="Sharp",
        curator="C",
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A", artist="X", position=0, intensity=0.1),
                    Artwork(id="a2", title="B", artist="Y", position=1, intensity=0.9),
                ],
            )
        ],
    )
    suggestions = suggest_transitions(ex, max_delta=0.35)
    assert suggestions[0].score < 0.5


def test_similarity_zero_different():
    a = _ex("1", genre="a", vitrine_score=10)
    b = _ex("2", genre="z", vitrine_score=90, curator="Other")
    assert exhibition_similarity(a, b) < 0.5
