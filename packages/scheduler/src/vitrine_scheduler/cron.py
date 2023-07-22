"""Cron field expansion and next_run scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CronField:
    values: set[int]
    min_val: int
    max_val: int


def _expand_part(part: str, min_val: int, max_val: int) -> set[int]:
    if part == "*":
        return set(range(min_val, max_val + 1))
    if part.startswith("*/"):
        step = int(part[2:])
        return set(range(min_val, max_val + 1, step))
    if "-" in part:
        start, end = part.split("-", 1)
        return set(range(int(start), int(end) + 1))
    if "," in part:
        return {int(x) for x in part.split(",")}
    return {int(part)}


@dataclass
class CronSchedule:
    minute: CronField
    hour: CronField
    day: CronField
    month: CronField
    weekday: CronField  # 0=Monday

    @classmethod
    def parse(cls, expression: str) -> "CronSchedule":
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression requires 5 fields")
        return cls(
            minute=CronField(_expand_part(parts[0], 0, 59), 0, 59),
            hour=CronField(_expand_part(parts[1], 0, 23), 0, 23),
            day=CronField(_expand_part(parts[2], 1, 31), 1, 31),
            month=CronField(_expand_part(parts[3], 1, 12), 1, 12),
            weekday=CronField(_expand_part(parts[4], 0, 6), 0, 6),
        )

    def matches(self, dt: datetime) -> bool:
        return (
            dt.minute in self.minute.values
            and dt.hour in self.hour.values
            and dt.day in self.day.values
            and dt.month in self.month.values
            and dt.weekday() in self.weekday.values
        )

    def next_run(self, after: datetime) -> datetime:
        """Find next matching datetime after `after` (exclusive), up to 4 years ahead."""
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = after + timedelta(days=366 * 4)
        while candidate <= limit:
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        raise ValueError("No matching run time found within search window")
