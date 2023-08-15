"""Shared rule engine types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from vitrine_types.models import Exhibition, Severity


@dataclass
class RuleViolation:
    rule: str
    message: str
    severity: Severity
    exhibition_id: str | None = None


@dataclass
class RuleResult:
    violations: list[RuleViolation]
    severity_counts: dict[str, int]


class RuleCheck(Protocol):
    def __call__(self, exhibition: Exhibition) -> list[RuleViolation]: ...
