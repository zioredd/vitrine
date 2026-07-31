from datetime import datetime, timedelta

import pytest

from vitrine_scheduler.cron import CronSchedule, _expand_part


def test_parse_star_every_minute():
    cron = CronSchedule.parse("* * * * *")
    assert len(cron.minute.values) == 60
    assert cron.minute.is_any is True


def test_parse_step():
    cron = CronSchedule.parse("*/15 * * * *")
    assert 0 in cron.minute.values
    assert 15 in cron.minute.values
    assert 45 in cron.minute.values
    assert cron.minute.is_any is True


def test_parse_range():
    cron = CronSchedule.parse("0 9-17 * * 1-5")
    assert cron.hour.values == frozenset(range(9, 18))
    assert cron.weekday.is_any is False


def test_matches_datetime():
    cron = CronSchedule.parse("30 14 * * *")
    dt = datetime(2026, 7, 21, 14, 30)
    assert cron.matches(dt)


def test_next_run_finds_future():
    cron = CronSchedule.parse("0 * * * *")
    after = datetime(2026, 7, 21, 14, 15)
    nxt = cron.next_run(after)
    assert nxt.hour == 15
    assert nxt.minute == 0


def test_next_run_every_minute():
    cron = CronSchedule.parse("* * * * *")
    after = datetime(2026, 1, 1, 0, 0)
    nxt = cron.next_run(after)
    assert nxt == datetime(2026, 1, 1, 0, 1)


def test_parse_list():
    cron = CronSchedule.parse("0,30 * * * *")
    assert cron.minute.values == frozenset({0, 30})
    assert cron.minute.is_any is False


# --- composite field expansion -------------------------------------------------


def test_expand_list_of_ranges():
    values, is_any = _expand_part("1-3,5", 0, 59)
    assert values == {1, 2, 3, 5}
    assert is_any is False


def test_expand_range_then_list():
    values, _ = _expand_part("1,3-5", 0, 59)
    assert values == {1, 3, 4, 5}


def test_expand_range_with_step():
    values, _ = _expand_part("1-10/2", 0, 59)
    assert values == {1, 3, 5, 7, 9}


def test_expand_star_range_with_step():
    values, is_any = _expand_part("*/10", 0, 59)
    assert 0 in values and 50 in values
    assert is_any is True


def test_expand_mixed_list_with_stepped_range():
    values, _ = _expand_part("0,10-20/5,55", 0, 59)
    assert values == {0, 10, 15, 20, 55}


def test_expand_inverted_range_raises():
    with pytest.raises(ValueError, match="Inverted"):
        _expand_part("5-1", 0, 59)


def test_expand_out_of_range_raises():
    with pytest.raises(ValueError, match="out of range"):
        _expand_part("0-60", 0, 59)


def test_expand_invalid_step_raises():
    with pytest.raises(ValueError, match="step"):
        _expand_part("1-10/0", 0, 59)


def test_parse_composite_minute_field():
    cron = CronSchedule.parse("1-3,5,10-16/2 * * * *")
    assert cron.minute.values == frozenset({1, 2, 3, 5, 10, 12, 14, 16})


# --- day / weekday OR semantics (Vixie cron) ------------------------------------


def test_day_and_weekday_or_when_both_constrained():
    """0 12 1 * 0 => noon on the 1st OR noon on Mondays (weekday 0=Monday)."""
    cron = CronSchedule.parse("0 12 1 * 0")
    # Monday 2024-01-08 is not the 1st — must still match via weekday
    assert cron.matches(datetime(2024, 1, 8, 12, 0))
    # Monday 2024-01-01 is the 1st — matches both
    assert cron.matches(datetime(2024, 1, 1, 12, 0))
    # Tuesday 2024-01-02 — neither
    assert not cron.matches(datetime(2024, 1, 2, 12, 0))


def test_day_only_when_weekday_any():
    cron = CronSchedule.parse("0 12 15 * *")
    assert cron.matches(datetime(2024, 3, 15, 12, 0))
    assert not cron.matches(datetime(2024, 3, 14, 12, 0))


def test_weekday_only_when_day_any():
    cron = CronSchedule.parse("0 9 * * 0")  # Mondays at 09:00
    assert cron.matches(datetime(2024, 1, 1, 9, 0))  # 2024-01-01 was Monday
    assert not cron.matches(datetime(2024, 1, 2, 9, 0))


def test_or_semantics_fire_count_vs_and():
    """Regression: AND under-fires; OR yields many more matches in a year."""
    cron = CronSchedule.parse("0 12 1 * 0")
    start = datetime(2024, 1, 1, 0, 0)
    hits = 0
    for i in range(366 * 24 * 60):
        dt = start + timedelta(minutes=i)
        if cron.matches(dt):
            hits += 1
    # 12 monthly 1sts at noon + ~52 Mondays at noon, minus overlap when 1st is Monday.
    # 2024-01-01 was Monday => 12 + 53 - 1 = 64 for a leap year with 53 Mondays.
    assert hits >= 60
    assert hits <= 70


def test_next_run_respects_weekday_or_day():
    cron = CronSchedule.parse("0 12 1 * 0")
    # After Jan 1 2024 noon (Monday the 1st), next should be next Monday Jan 8
    after = datetime(2024, 1, 1, 12, 0)
    nxt = cron.next_run(after)
    assert nxt == datetime(2024, 1, 8, 12, 0)


def test_next_run_across_month_boundary_for_dom():
    cron = CronSchedule.parse("0 0 1 * *")
    after = datetime(2024, 1, 15, 10, 0)
    nxt = cron.next_run(after)
    assert nxt == datetime(2024, 2, 1, 0, 0)


def test_rejects_wrong_field_count():
    with pytest.raises(ValueError, match="5 fields"):
        CronSchedule.parse("* * *")
