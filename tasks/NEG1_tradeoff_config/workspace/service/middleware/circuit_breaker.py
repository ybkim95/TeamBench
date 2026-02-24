"""Circuit breaker for external service calls — NOT IMPLEMENTED."""
import time
import random


# Simulated external service
def _external_service(data):
    """Simulate an external service call."""
    # Randomly fail ~10% of the time
    if random.random() < 0.1:
        raise ConnectionError("External service unavailable")
    time.sleep(0.01)  # 10ms latency
    return {"processed": True, "input_hash": hash(str(data))}


def call_external_service(data):
    """Call external service — no circuit breaker, no retry."""
    try:
        return _external_service(data)
    except ConnectionError:
        return {"processed": False, "error": "service_unavailable"}
