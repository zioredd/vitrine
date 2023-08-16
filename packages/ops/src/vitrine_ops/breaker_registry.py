"""Multi-breaker registry for circuit breaker management."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from vitrine_ops.governance import CircuitBreaker, CircuitState


class BreakerPolicy(str, Enum):
    FAIL_FAST = "fail_fast"
    FALLBACK = "fallback"
    RETRY = "retry"


@dataclass
class BreakerConfig:
    name: str
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0
    policy: BreakerPolicy = BreakerPolicy.FAIL_FAST
    fallback_value: object = None


@dataclass
class BreakerStats:
    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: float
    total_calls: int
    rejected_calls: int


@dataclass
class BreakerEvent:
    breaker_name: str
    event_type: str
    timestamp: float
    detail: str = ""


class BreakerRegistry:
    """Manage named circuit breakers with shared observability."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._configs: dict[str, BreakerConfig] = {}
        self._success_counts: dict[str, int] = {}
        self._total_calls: dict[str, int] = {}
        self._rejected: dict[str, int] = {}
        self._events: list[BreakerEvent] = []
        self._listeners: list[Callable[[BreakerEvent], None]] = []

    def register(self, config: BreakerConfig) -> None:
        self._breakers[config.name] = CircuitBreaker(
            failure_threshold=config.failure_threshold,
            recovery_timeout_sec=config.recovery_timeout_sec,
        )
        self._configs[config.name] = config
        self._success_counts.setdefault(config.name, 0)
        self._total_calls.setdefault(config.name, 0)
        self._rejected.setdefault(config.name, 0)

    def get(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            raise KeyError(f"breaker '{name}' not registered")
        return self._breakers[name]

    def _emit(self, name: str, event_type: str, detail: str = "") -> None:
        event = BreakerEvent(name, event_type, time.monotonic(), detail)
        self._events.append(event)
        for listener in self._listeners:
            listener(event)

    def record_success(self, name: str) -> None:
        cb = self.get(name)
        cb.record_success()
        self._success_counts[name] = self._success_counts.get(name, 0) + 1
        self._emit(name, "success")

    def record_failure(self, name: str, detail: str = "") -> None:
        cb = self.get(name)
        prev_state = cb.state
        cb.record_failure()
        if cb.state == CircuitState.OPEN and prev_state != CircuitState.OPEN:
            self._emit(name, "opened", detail)
        else:
            self._emit(name, "failure", detail)

    def allow(self, name: str) -> bool:
        cb = self.get(name)
        self._total_calls[name] = self._total_calls.get(name, 0) + 1
        allowed = cb.allow_request()
        if not allowed:
            self._rejected[name] = self._rejected.get(name, 0) + 1
            self._emit(name, "rejected")
        return allowed

    def call(self, name: str, fn: Callable[[], object], fallback: Callable[[], object] | None = None) -> object:
        """Execute fn through breaker with optional fallback."""
        config = self._configs.get(name)
        if not self.allow(name):
            if config and config.policy == BreakerPolicy.FALLBACK:
                fb = fallback or (lambda: config.fallback_value)
                return fb()
            raise RuntimeError(f"circuit breaker '{name}' is open")

        try:
            result = fn()
            self.record_success(name)
            return result
        except Exception as exc:
            self.record_failure(name, str(exc))
            if config and config.policy == BreakerPolicy.FALLBACK:
                fb = fallback or (lambda: config.fallback_value)
                return fb()
            raise

    def stats(self, name: str) -> BreakerStats:
        cb = self.get(name)
        return BreakerStats(
            name=name,
            state=cb.state,
            failure_count=cb.failure_count,
            success_count=self._success_counts.get(name, 0),
            last_failure_time=cb.last_failure_time,
            total_calls=self._total_calls.get(name, 0),
            rejected_calls=self._rejected.get(name, 0),
        )

    def all_stats(self) -> list[BreakerStats]:
        return [self.stats(name) for name in self._breakers]

    def open_breakers(self) -> list[str]:
        return [name for name, cb in self._breakers.items() if cb.state == CircuitState.OPEN]

    def reset(self, name: str) -> None:
        cb = self.get(name)
        cb.record_success()
        self._emit(name, "reset")

    def reset_all(self) -> None:
        for name in list(self._breakers):
            self.reset(name)

    def add_listener(self, listener: Callable[[BreakerEvent], None]) -> None:
        self._listeners.append(listener)

    def recent_events(self, limit: int = 50) -> list[BreakerEvent]:
        return self._events[-limit:]

    def health_summary(self) -> dict[str, object]:
        stats = self.all_stats()
        open_count = len(self.open_breakers())
        total_rejected = sum(s.rejected_calls for s in stats)
        return {
            "breaker_count": len(stats),
            "open_count": open_count,
            "healthy": open_count == 0,
            "total_rejected": total_rejected,
            "breakers": [
                {"name": s.name, "state": s.state.value, "failures": s.failure_count}
                for s in stats
            ],
        }


def default_registry() -> BreakerRegistry:
    """Registry pre-populated with common service breakers."""
    registry = BreakerRegistry()
    for name in ("catalog", "ingest", "graph", "ai", "enterprise"):
        registry.register(BreakerConfig(name=name, failure_threshold=5, recovery_timeout_sec=30.0))
    return registry
