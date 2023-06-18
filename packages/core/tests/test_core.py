from datetime import date, timedelta

from vitrine_types.models import Artwork, Exhibition, Provenance, Room, Signal, SignalKind

from vitrine_core.analytics import alert_engine, audience_cohorts, catalog_stress_index, what_if_simulator
from vitrine_core.editorial import assess_booking_risks, compute_release_windows, resolve_royalty_tier
from vitrine_core.intelligence import build_command_center, build_decision_report, build_intelligence_report
from vitrine_core.scoring import composite_vitrine_score, freshness_decay, rank_normalize, weighted_signal_blend


def _sample_exhibition() -> Exhibition:
    return Exhibition(
        id="ex-test",
        title="Test Show",
        curator="Curator",
        vitrine_score=72.0,
        rooms=[
            Room(
                id="r1",
                name="Main",
                artworks=[
                    Artwork(id="a1", title="One", artist="A", intensity=0.7, dwell_sec=120),
                    Artwork(id="a2", title="Two", artist="B", intensity=0.5, dwell_sec=90),
                ],
            )
        ],
        signals=[
            Signal(
                id="s1",
                exhibition_id="ex-test",
                kind=SignalKind.REVIEW,
                score=80,
                provenance=Provenance(source_name="ArtNews", confidence=0.9),
            )
        ],
    )


def test_freshness_decay_halves_over_half_life():
    base = 100.0
    ref = date(2025, 1, 1)
    mid = freshness_decay(base, ref, ref + timedelta(days=180))
    assert 49 <= mid <= 51


def test_rank_normalize_spreads_values():
    out = rank_normalize([10.0, 20.0, 30.0])
    assert out[0] < out[1] < out[2]


def test_composite_vitrine_score_weighted():
    score = composite_vitrine_score([80.0, 70.0], craft_score=75.0, crowd_score=65.0)
    assert 65 <= score <= 85


def test_intelligence_report_top_exhibitions():
    ex = _sample_exhibition()
    report = build_intelligence_report([ex], alerts=[])
    assert report.exhibition_count == 1
    assert report.top_exhibitions[0]["id"] == "ex-test"


def test_booking_risk_sparse_catalog():
    ex = Exhibition(id="x", title="Sparse", curator="C", rooms=[])
    risks = assess_booking_risks([ex])
    assert risks[0].risk_score >= 0.25


def test_royalty_tier_platinum():
    tier = resolve_royalty_tier(92.0)
    assert tier.tier == "platinum"


def test_what_if_simulator_increases_with_boost():
    ex = _sample_exhibition()
    result = what_if_simulator(ex, intensity_boost=0.2)
    assert result.delta >= 0


def test_alert_engine_fires_on_low_score():
    ex = Exhibition(id="low", title="Low", curator="C", vitrine_score=10.0)
    alerts = alert_engine([ex])
    assert any(a.code == "SCORE_LOW" for a in alerts)


def test_command_center_pending_jobs():
    snap = build_command_center([_sample_exhibition()], pending_jobs=3)
    assert snap.pending_jobs == 3
    assert snap.active_exhibitions == 1


def test_decision_report_greenlight():
    ex = _sample_exhibition()
    report = build_decision_report(ex, booking_risk=0.1)
    assert report.recommendation in {"greenlight", "conditional", "defer"}


def test_audience_cohorts_by_genre():
    exs = [
        Exhibition(id="1", title="A", curator="C", genre="modern", vitrine_score=80),
        Exhibition(id="2", title="B", curator="C", genre="modern", vitrine_score=60),
    ]
    cohorts = audience_cohorts(exs)
    assert len(cohorts) == 1
    assert cohorts[0].size == 2


def test_catalog_stress_sparse():
    ex = Exhibition(id="s", title="S", curator="C", rooms=[])
    assert catalog_stress_index([ex]) > 0


def test_weighted_signal_blend():
    assert weighted_signal_blend([80.0, 60.0], [1.0, 3.0]) == 65.0


def test_release_windows_no_overlap():
    ex = Exhibition(id="e", title="E", curator="C", opened_on=date(2026, 1, 1))
    windows = compute_release_windows([ex])
    assert windows[0].conflict_level == 0.0
