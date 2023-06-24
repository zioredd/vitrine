from vitrine_types.models import Artwork, Exhibition, Room

from vitrine_catalog.repository import CatalogFilter, CatalogRepository


def _make_ex(id_: str, **kwargs) -> Exhibition:
    defaults = {"title": id_, "curator": "C"}
    defaults.update(kwargs)
    return Exhibition(id=id_, **defaults)


def test_from_seed_empty_when_no_seed_module():
    repo = CatalogRepository.from_seed()
    assert isinstance(repo.load_all(), list)


def test_get_by_id():
    ex = _make_ex("ex-1", vitrine_score=80.0)
    repo = CatalogRepository.from_list([ex])
    assert repo.get_by_id("ex-1") is ex
    assert repo.get_by_id("missing") is None


def test_filter_by_residency():
    exs = [
        _make_ex("1", residency="MoCA"),
        _make_ex("2", residency="Tate"),
    ]
    repo = CatalogRepository.from_list(exs)
    out = repo.filter(CatalogFilter(residency="MoCA"))
    assert len(out) == 1
    assert out[0].id == "1"


def test_filter_min_score():
    exs = [_make_ex("1", vitrine_score=90), _make_ex("2", vitrine_score=40)]
    repo = CatalogRepository.from_list(exs)
    out = repo.filter(CatalogFilter(min_score=80))
    assert len(out) == 1


def test_count_artworks():
    ex = Exhibition(
        id="x",
        title="X",
        curator="C",
        rooms=[Room(id="r", name="R", artworks=[Artwork(id="a", title="A", artist="X")])],
    )
    repo = CatalogRepository.from_list([ex])
    assert repo.count_artworks() == 1


def test_upsert_and_delete():
    repo = CatalogRepository.from_list([_make_ex("1")])
    repo.upsert(_make_ex("1", title="Updated"))
    assert repo.get_by_id("1").title == "Updated"
    assert repo.delete("1")
    assert repo.get_by_id("1") is None


def test_filter_by_genre_and_series():
    exs = [
        _make_ex("1", genre="modern", series="Spring"),
        _make_ex("2", genre="modern", series="Fall"),
    ]
    repo = CatalogRepository.from_list(exs)
    out = repo.filter(CatalogFilter(genre="modern", series="Spring"))
    assert len(out) == 1
