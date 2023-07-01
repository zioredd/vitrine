from vitrine_types.models import Artwork, Exhibition, Room

from vitrine_mix.craft import (
    build_craft_report,
    energy_map,
    pacing_curve,
    pacing_score,
    transition_density,
    wall_text_craft,
)


def _artworks(*specs: tuple[int, float, float]) -> list[Artwork]:
    return [
        Artwork(id=f"a{i}", title=f"A{i}", artist="X", position=p, intensity=inten, dwell_sec=dwell, wall_text_ratio=0.35)
        for i, (p, inten, dwell) in enumerate(specs)
    ]


def test_pacing_curve_cumulative_dwell():
    arts = _artworks((0, 0.5, 10), (1, 0.7, 20))
    curve = pacing_curve(arts)
    assert curve[1].cumulative_dwell == 30.0


def test_energy_map_zones():
    arts = _artworks((0, 0.8, 10), (1, 0.9, 10), (2, 0.2, 10))
    zones = energy_map(arts, zone_size=2)
    assert len(zones) >= 1
    assert zones[0].label == "peak"


def test_transition_density():
    arts = _artworks((0, 0.2, 10), (1, 0.8, 10), (2, 0.5, 10))
    m = transition_density(arts)
    assert m.count == 2
    assert m.max_delta >= 0.5


def test_pacing_score_range():
    arts = _artworks((0, 0.3, 10), (1, 0.5, 10), (2, 0.7, 10), (3, 0.4, 10))
    score = pacing_score(arts)
    assert 0 <= score <= 100


def test_wall_text_craft_optimal():
    arts = [Artwork(id="a", title="A", artist="X", wall_text_ratio=0.35)]
    assert wall_text_craft(arts) == 100.0


def test_build_craft_report():
    ex = Exhibition(
        id="ex",
        title="Mix",
        curator="C",
        rooms=[Room(id="r", name="R", artworks=_artworks((0, 0.4, 10), (1, 0.6, 10)))],
    )
    report = build_craft_report(ex)
    assert report.pacing_score >= 0
    assert len(report.energy_zones) >= 1


def test_transition_density_single_artwork():
    m = transition_density([Artwork(id="a", title="A", artist="X")])
    assert m.count == 0
