"""Fault injection test: checks circuit breaker behavior."""
import sys
import os

sys.path.insert(0, ".")


def run_reliability_test():
    """Test circuit breaker behavior."""
    issues = []

    # Check config
    import json
    with open("service/config.json") as f:
        config = json.load(f)

    if not config.get("circuit_breaker_enabled", False):
        issues.append("circuit_breaker_not_enabled")

    # Check circuit breaker implementation
    from service.middleware.circuit_breaker import call_external_service

    # Test 1: Normal operation should work
    result = call_external_service({"test": 1})
    if not isinstance(result, dict):
        issues.append("circuit_breaker_no_response")

    # Test 2: After consecutive failures, circuit should open
    failure_count = 0
    for _ in range(5):
        try:
            call_external_service({"trigger_fail": True})
        except Exception:
            failure_count += 1
    if failure_count < 3:
        issues.append("no_circuit_breaker_logic")

    # Test 3: After circuit opens, should reject quickly (not hang)
    import time
    start = time.time()
    try:
        call_external_service({"test": 2})
    except Exception:
        pass
    elapsed = time.time() - start
    if elapsed > 0.5:
        issues.append("no_backoff")

    if issues:
        print(f"RELIABILITY_FAIL: {issues}")
        sys.exit(1)
    else:
        print("RELIABILITY_PASS: All checks passed")
        sys.exit(0)


if __name__ == "__main__":
    run_reliability_test()
