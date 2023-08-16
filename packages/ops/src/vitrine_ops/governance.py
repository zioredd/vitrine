"""Policy engine, circuit breaker, audit hash chain, feature flags."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class PolicyRule:
    name: str
    condition: Callable[[dict[str, Any]], bool]
    action: str


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        self.rules = rules or []

    def evaluate(self, context: dict[str, Any]) -> list[str]:
        actions: list[str] = []
        for rule in self.rules:
            if rule.condition(context):
                actions.append(rule.action)
        return actions


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    recovery_timeout_sec: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # half-open: allow probe


@dataclass
class AuditEntry:
    sequence: int
    action: str
    payload_hash: str
    prev_hash: str
    entry_hash: str


class AuditChain:
    """Tamper-evident hash chain for audit log."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._genesis = hashlib.sha256(b"vitrine-genesis").hexdigest()

    def append(self, action: str, payload: dict[str, Any]) -> AuditEntry:
        seq = len(self._entries) + 1
        payload_hash = hashlib.sha256(repr(sorted(payload.items())).encode()).hexdigest()
        prev = self._entries[-1].entry_hash if self._entries else self._genesis
        entry_hash = hashlib.sha256(f"{seq}|{action}|{payload_hash}|{prev}".encode()).hexdigest()
        entry = AuditEntry(
            sequence=seq,
            action=action,
            payload_hash=payload_hash,
            prev_hash=prev,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        return verify_chain_detailed(self).valid

    def __len__(self) -> int:
        return len(self._entries)


@dataclass
class ChainVerificationIssue:
    sequence: int
    issue_type: str
    message: str
    expected: str | None = None
    actual: str | None = None


@dataclass
class ChainVerificationResult:
    valid: bool
    entry_count: int
    issues: list[ChainVerificationIssue]
    genesis_hash: str
    terminal_hash: str | None

    @property
    def first_issue(self) -> ChainVerificationIssue | None:
        return self.issues[0] if self.issues else None


def verify_chain_detailed(chain: AuditChain) -> ChainVerificationResult:
    """Verify audit hash chain with per-entry diagnostics."""
    genesis = chain._genesis
    prev = genesis
    issues: list[ChainVerificationIssue] = []
    terminal: str | None = None

    for entry in chain._entries:
        expected_hash = hashlib.sha256(
            f"{entry.sequence}|{entry.action}|{entry.payload_hash}|{prev}".encode()
        ).hexdigest()

        if entry.prev_hash != prev:
            issues.append(
                ChainVerificationIssue(
                    sequence=entry.sequence,
                    issue_type="prev_hash_mismatch",
                    message=f"entry {entry.sequence} prev_hash does not link to prior entry",
                    expected=prev,
                    actual=entry.prev_hash,
                )
            )

        if entry.entry_hash != expected_hash:
            issues.append(
                ChainVerificationIssue(
                    sequence=entry.sequence,
                    issue_type="entry_hash_mismatch",
                    message=f"entry {entry.sequence} hash recomputation failed",
                    expected=expected_hash,
                    actual=entry.entry_hash,
                )
            )

        if entry.sequence != len(issues) + entry.sequence - len(
            [i for i in issues if i.sequence <= entry.sequence]
        ):
            pass  # sequence gaps checked separately

        expected_seq = len([e for e in chain._entries if e.sequence <= entry.sequence])
        if entry.sequence != expected_seq and entry.sequence != len(
            [e for e in chain._entries[: chain._entries.index(entry) + 1]]
        ):
            idx = chain._entries.index(entry)
            if entry.sequence != idx + 1:
                issues.append(
                    ChainVerificationIssue(
                        sequence=entry.sequence,
                        issue_type="sequence_gap",
                        message=f"expected sequence {idx + 1}, got {entry.sequence}",
                        expected=str(idx + 1),
                        actual=str(entry.sequence),
                    )
                )

        prev = entry.entry_hash
        terminal = entry.entry_hash

    return ChainVerificationResult(
        valid=len(issues) == 0,
        entry_count=len(chain._entries),
        issues=issues,
        genesis_hash=genesis,
        terminal_hash=terminal,
    )


class FeatureFlags:
    def __init__(self, flags: dict[str, bool] | None = None) -> None:
        self._flags: dict[str, bool] = dict(flags or {})

    def is_enabled(self, name: str, default: bool = False) -> bool:
        return self._flags.get(name, default)

    def enable(self, name: str) -> None:
        self._flags[name] = True

    def disable(self, name: str) -> None:
        self._flags[name] = False

    def evaluate_for_context(self, name: str, context: dict[str, Any]) -> bool:
        if not self.is_enabled(name):
            return False
        rollout = context.get("rollout_pct", 100)
        user_bucket = hash(context.get("user_id", "")) % 100
        return user_bucket < rollout
