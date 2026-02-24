"""Input validation middleware — currently too slow."""
import time
import re


def validate_input(data):
    """Validate request input data.

    Current implementation: uses heavyweight parsing approach.
    Takes ~200ms per validation call.
    """
    errors = []

    # Simulate slow validation (heavyweight approach)
    # In production, this would be calling an external validation service
    # or doing complex schema validation
    time.sleep(0.2)  # 200ms — this is the performance bottleneck

    # Basic field checks
    if not isinstance(data, dict):
        errors.append("input_must_be_object")
        return False, errors

    name = data.get("name", "")
    if not name or len(name) > 200:
        errors.append("invalid_name")

    email = data.get("email", "")
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors.append("invalid_email")

    value = data.get("value")
    if value is not None:
        try:
            v = float(value)
            if v < 0 or v > 1000000:
                errors.append("value_out_of_range")
        except (ValueError, TypeError):
            errors.append("invalid_value")

    return len(errors) == 0, errors
