"""Expanded ops module tests."""

from __future__ import annotations

from vitrine_ops.breaker_registry import BreakerConfig, BreakerPolicy, BreakerRegistry, default_registry
from vitrine_ops.governance import AuditChain, verify_chain_detailed
from vitrine_ops.policy_dsl import PolicyDSLEngine, PolicyRuleSpec, evaluate_policy, parse_policy, validate_expression


def test_evaluate_policy_and():
    assert evaluate_policy("score > 80 AND role = curator", {"score": 90, "role": "curator"})
    assert not evaluate_policy("score > 80 AND role = curator", {"score": 70, "role": "curator"})


def test_evaluate_policy_or():
    assert evaluate_policy("score > 90 OR role = admin", {"score": 50, "role": "admin"})


def test_evaluate_policy_not():
    assert not evaluate_policy("NOT blocked = true", {"blocked": True})
    assert evaluate_policy("NOT blocked = true", {"blocked": False})


def test_evaluate_policy_comparisons():
    assert evaluate_policy("score >= 80", {"score": 80})
    assert evaluate_policy("score < 50", {"score": 30})


def test_parse_policy_tokens():
    result = parse_policy("score > 80 AND role = curator")
    assert result.ast is not None


def test_validate_expression_invalid():
    errors = validate_expression("score > > 80")
    assert len(errors) >= 1


def test_policy_dsl_engine():
    engine = PolicyDSLEngine(
        rules=[
            PolicyRuleSpec("high", "score > 80", "approve"),
            PolicyRuleSpec("low", "score < 50", "reject"),
        ]
    )
    actions = engine.evaluate({"score": 90})
    assert "approve" in actions


def test_breaker_registry_allow():
    registry = BreakerRegistry()
    registry.register(BreakerConfig(name="test", failure_threshold=2))
    assert registry.allow("test")


def test_breaker_registry_opens():
    registry = BreakerRegistry()
    registry.register(BreakerConfig(name="svc", failure_threshold=2))
    registry.record_failure("svc")
    registry.record_failure("svc")
    assert not registry.allow("svc")


def test_breaker_registry_call_with_fallback():
    registry = BreakerRegistry()
    registry.register(
        BreakerConfig(name="api", failure_threshold=1, policy=BreakerPolicy.FALLBACK, fallback_value={"ok": False})
    )
    registry.record_failure("api")
    result = registry.call("api", lambda: {"ok": True})
    assert result == {"ok": False}


def test_default_registry_health():
    registry = default_registry()
    summary = registry.health_summary()
    assert summary["breaker_count"] == 5


def test_verify_chain_detailed_valid():
    chain = AuditChain()
    chain.append("create", {"id": "1"})
    chain.append("update", {"id": "1"})
    result = verify_chain_detailed(chain)
    assert result.valid
    assert result.entry_count == 2


def test_verify_chain_detailed_tampered():
    chain = AuditChain()
    chain.append("create", {"id": "1"})
    chain._entries[0].action = "delete"
    result = verify_chain_detailed(chain)
    assert not result.valid
    assert len(result.issues) >= 1
