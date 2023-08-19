from vitrine_ops.governance import AuditChain, CircuitBreaker, CircuitState, FeatureFlags, PolicyEngine, PolicyRule


def test_policy_engine_fires_matching_rules():
    engine = PolicyEngine(
        rules=[
            PolicyRule("high_risk", lambda ctx: ctx.get("risk", 0) > 0.5, "block"),
            PolicyRule("low_score", lambda ctx: ctx.get("score", 100) < 50, "review"),
        ]
    )
    actions = engine.evaluate({"risk": 0.8, "score": 30})
    assert "block" in actions
    assert "review" in actions


def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert not cb.allow_request()


def test_circuit_breaker_resets_on_success():
    cb = CircuitBreaker()
    cb.record_failure()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_audit_chain_verify():
    chain = AuditChain()
    chain.append("create", {"id": "1"})
    chain.append("update", {"id": "1", "score": 90})
    assert chain.verify()
    assert len(chain) == 2


def test_audit_chain_tamper_detected():
    chain = AuditChain()
    chain.append("create", {"id": "1"})
    chain._entries[0].action = "delete"
    assert not chain.verify()


def test_feature_flags_enable_disable():
    flags = FeatureFlags({"beta": True})
    assert flags.is_enabled("beta")
    flags.disable("beta")
    assert not flags.is_enabled("beta")


def test_feature_flags_rollout():
    flags = FeatureFlags({"new_ui": True})
    enabled = flags.evaluate_for_context("new_ui", {"user_id": "user-1", "rollout_pct": 100})
    assert enabled
