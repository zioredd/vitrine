"""Cron field expansion and next_run scheduling.

Field grammar (per field):
  *           all values in range
  */N         every Nth value from min
  A-B         inclusive range
  A-B/N       range with step
  A,B,C       list (items may themselves be ranges or stepped ranges)
  N           single value

Day-of-month / weekday semantics follow Vixie cron:
  When *both* day-of-month and weekday are constrained (not ``*`` / ``*/N``
  covering the full domain as an any-field), a datetime matches if **either**
  field matches (OR). When only one is constrained, that field alone applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class CronField:
    values: frozenset[int]
    min_val: int
    max_val: int
    # True when the original token was a wildcard (* or */N over the full domain)
    is_any: bool = False


def _parse_atom(atom: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single list item: N, A-B, or A-B/N (also */N handled by caller)."""
    step = 1
    body = atom
    if "/" in atom:
        body, step_s = atom.split("/", 1)
        if not step_s.isdigit() or int(step_s) < 1:
            raise ValueError(f"Invalid cron step in '{atom}'")
        step = int(step_s)

    if body == "*":
        start, end = min_val, max_val
    elif "-" in body:
        start_s, end_s = body.split("-", 1)
        if not start_s.lstrip("-").isdigit() or not end_s.lstrip("-").isdigit():
            raise ValueError(f"Invalid cron range in '{atom}'")
        start, end = int(start_s), int(end_s)
        if start > end:
            raise ValueError(f"Inverted cron range '{atom}' (start > end)")
    else:
        if not body.lstrip("-").isdigit():
            raise ValueError(f"Invalid cron value '{atom}'")
        start = end = int(body)

    if start < min_val or end > max_val:
        raise ValueError(
            f"Cron value '{atom}' out of range [{min_val}, {max_val}]"
        )

    return set(range(start, end + 1, step))


def _expand_part(part: str, min_val: int, max_val: int) -> tuple[set[int], bool]:
    """Expand one cron field. Returns (values, is_any_wildcard)."""
    part = part.strip()
    if not part:
        raise ValueError("Empty cron field")

    # Bare wildcard or stepped wildcard over the full domain => "any"
    if part == "*" or (part.startswith("*/") and "," not in part and "-" not in part):
        values = _parse_atom(part if "/" in part else "*", min_val, max_val)
        return values, True

    values: set[int] = set()
    for atom in part.split(","):
        atom = atom.strip()
        if not atom:
            raise ValueError(f"Invalid empty atom in cron field '{part}'")
        values |= _parse_atom(atom, min_val, max_val)

    if not values:
        raise ValueError(f"Cron field '{part}' expands to empty set")
    return values, False


def _field(part: str, min_val: int, max_val: int) -> CronField:
    values, is_any = _expand_part(part, min_val, max_val)
    return CronField(frozenset(values), min_val, max_val, is_any=is_any)


@dataclass
class CronSchedule:
    minute: CronField
    hour: CronField
    day: CronField
    month: CronField
    weekday: CronField  # 0=Monday .. 6=Sunday (Python datetime.weekday)
    expression: str = ""

    @classmethod
    def parse(cls, expression: str) -> "CronSchedule":
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError("Cron expression requires 5 fields")
        return cls(
            minute=_field(parts[0], 0, 59),
            hour=_field(parts[1], 0, 23),
            day=_field(parts[2], 1, 31),
            month=_field(parts[3], 1, 12),
            weekday=_field(parts[4], 0, 6),
            expression=expression.strip(),
        )

    def matches(self, dt: datetime) -> bool:
        if dt.minute not in self.minute.values:
            return False
        if dt.hour not in self.hour.values:
            return False
        if dt.month not in self.month.values:
            return False

        day_ok = dt.day in self.day.values
        weekday_ok = dt.weekday() in self.weekday.values

        # Vixie cron: when both day-of-month and weekday are constrained,
        # match if either matches. Otherwise require the constrained field(s).
        if not self.day.is_any and not self.weekday.is_any:
            return day_ok or weekday_ok
        if not self.day.is_any:
            return day_ok
        if not self.weekday.is_any:
            return weekday_ok
        return True

    def next_run(self, after: datetime) -> datetime:
        """Find next matching datetime after `after` (exclusive), up to 4 years ahead."""
        candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = after + timedelta(days=366 * 4)
        while candidate <= limit:
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        raise ValueError("No matching run time found within search window")
