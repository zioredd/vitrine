from datetime import datetime

from vitrine_scheduler.cron import CronSchedule


def test_parse_star_every_minute():
    cron = CronSchedule.parse("* * * * *")
    assert len(cron.minute.values) == 60


def test_parse_step():
    cron = CronSchedule.parse("*/15 * * * *")
    assert 0 in cron.minute.values
    assert 15 in cron.minute.values


def test_parse_range():
    cron = CronSchedule.parse("0 9-17 * * 1-5")
    assert cron.hour.values == set(range(9, 18))


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
    assert cron.minute.values == {0, 30}
