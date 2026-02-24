"""Security checker: validates TLS, input validation, etc."""
import json
import sys
import os


def run_security_scan():
    """Check security requirements."""
    issues = []

    # Check config
    config_path = "service/config.json"
    with open(config_path) as f:
        config = json.load(f)

    # 1. TLS must be enabled
    if not config.get("tls_enabled", False):
        issues.append("tls_disabled")

    # 2. Input validation must be enabled
    if not config.get("validate_input", True):
        issues.append("validation_disabled")

    # 3. Check validator is functional
    sys.path.insert(0, ".")
    from service.middleware.validator import validate_input
    if not callable(validate_input):
        issues.append("validator_not_callable")

    if issues:
        print(f"SECURITY_FAIL: {issues}")
        sys.exit(1)
    else:
        print("SECURITY_PASS: All checks passed")
        sys.exit(0)


if __name__ == "__main__":
    run_security_scan()
