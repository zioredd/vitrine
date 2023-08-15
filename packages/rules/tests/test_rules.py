from vitrine_types.models import Artwork, Exhibition, Provenance, Room, Signal, SignalKind

from vitrine_rules.engine import run_rules


def _ex(**kwargs) -> Exhibition:
    defaults = {"id": "ex-1", "title": "Valid Title", "curator": "C"}
    defaults.update(kwargs)
    return Exhibition(**defaults)


def test_title_identity_fails_short():
    result = run_rules([_ex(title="AB")])
    assert any(v.rule == "title_identity" for v in result.violations)


def test_signal_balance_warns_single_signal():
    ex = _ex(signals=[Signal(id="s", exhibition_id="ex-1", kind=SignalKind.REVIEW, score=80, provenance=Provenance(source_name="X", confidence=0.9))])
    result = run_rules([ex])
    assert any(v.rule == "signal_balance" for v in result.violations)


def test_provenance_low_confidence():
    ex = _ex(
        signals=[
            Signal(
                id="s",
                exhibition_id="ex-1",
                kind=SignalKind.REVIEW,
                score=80,
                provenance=Provenance(source_name="X", confidence=0.2),
            )
        ]
    )
    result = run_rules([ex])
    assert any(v.rule == "provenance_confidence" for v in result.violations)


def test_intensity_range():
    ex = _ex(
        rooms=[Room(id="r", name="R", artworks=[Artwork(id="a", title="A", artist="X", intensity=0.01)])]
    )
    result = run_rules([ex])
    assert any(v.rule == "intensity_range" for v in result.violations)


def test_severity_counts():
    result = run_rules([_ex(title="X"), _ex(id="ex-2", title="Y")])
    assert isinstance(result.severity_counts, dict)


def test_clean_exhibition_few_violations():
    ex = _ex(
        rooms=[
            Room(
                id="r",
                name="R",
                artworks=[
                    Artwork(id="a1", title="A", artist="X", intensity=0.5, position=0),
                    Artwork(id="a2", title="B", artist="Y", intensity=0.6, position=1),
                ],
            )
        ],
        signals=[
            Signal(id="s1", exhibition_id="ex-1", kind=SignalKind.REVIEW, score=80, provenance=Provenance(source_name="A", confidence=0.9, source_url="http://x", rank=1)),
            Signal(id="s2", exhibition_id="ex-1", kind=SignalKind.VISITOR, score=75, provenance=Provenance(source_name="B", confidence=0.8, source_url="http://y", rank=2)),
        ],
    )
    result = run_rules([ex])
    assert not any(v.severity.value == "error" for v in result.violations)


def test_rank_consistency():
    ex = _ex(
        signals=[
            Signal(id="s1", exhibition_id="ex-1", kind=SignalKind.REVIEW, score=80, provenance=Provenance(source_name="A", confidence=0.9, rank=2)),
            Signal(id="s2", exhibition_id="ex-1", kind=SignalKind.VISITOR, score=75, provenance=Provenance(source_name="B", confidence=0.8, rank=1)),
        ]
    )
    result = run_rules([ex])
    assert any(v.rule == "rank_consistency" for v in result.violations)
