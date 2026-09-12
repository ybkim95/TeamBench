"""
payment_service.py — e-commerce order processing service component

Part of a distributed system processing e-commerce order processing requests.
This service coordinates with peer services using shared threading locks.

Seed: 0
"""
import threading
import time
import logging
import hashlib
import itertools
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(threadName)s: %(message)s",
)
logger = logging.getLogger("payment_service")

# ── Shared locks (must be imported/shared across services in production) ──────
# In this simulation each file declares its own instances for standalone testing.
# In the real system these are shared via a lock registry.
lock_inventory = threading.Lock()  # protects the global inventory counter
lock_payment = threading.Lock()  # protects the payment ledger

# ── Configuration ─────────────────────────────────────────────────────────────
PORT = 8630
WORKER_THREADS = 6
MAX_QUEUE_SIZE = 256

# ── Work queue (simulated) ────────────────────────────────────────────────────
_work_queue: List[Dict] = []
_work_queue_lock = threading.Lock()

# ── Red herring: looks suspicious in thread dumps but is NOT the deadlock ─────
def _poll_queue_payment_service(self) -> None:
    """
    Back-pressure poller: busy-waits until the work queue drains below
    the high-water mark.  Appears as 100%% CPU in thread dumps — this is
    intentional and is NOT the cause of the service hang.
    """
    high_water = 50
    while len(self._work_queue) > high_water:
        pass  # Intentional busy-wait (red herring — NOT the deadlock)
    # Queue has drained; normal processing resumes


# ── Core service class ────────────────────────────────────────────────────────

class PaymentService:
    """Main service class for payment service."""

    def __init__(self) -> None:
        self._work_queue: List[Dict] = []
        self._running = False
        self._request_counter = itertools.count(1)

    def _generate_request_id(self) -> str:
        n = next(self._request_counter)
        return hashlib.md5(f"req-{n}-payment_service-seed-0".encode()).hexdigest()[:12]

    def process_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming request, acquiring shared locks as required.

        Lock acquisition order determines deadlock safety.
        # Correct acquisition order: lock_inventory THEN lock_payment.
    # All services must acquire in this order to prevent deadlock.
        """
        request_id = self._generate_request_id()
        logger.debug("Processing request_id=%s payload_keys=%s", request_id, list(payload.keys()))

        with lock_inventory:
            # Critical section: operating on lock_inventory
            logger.debug("Acquired lock_inventory for request_id=%s", request_id)
            time.sleep(0.001)  # Simulate work under first lock

            with lock_payment:
                # Critical section: operating on both lock_inventory and lock_payment
                logger.debug("Acquired lock_payment for request_id=%s", request_id)
                result = self._do_work(payload, request_id)

        return result

    def _do_work(self, payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Perform the actual work while both locks are held."""
        return {
            "request_id": request_id,
            "service": "payment_service",
            "status": "ok",
            "payload_keys": list(payload.keys()),
            "processed_by": "payment_service",
        }

    def health_check(self) -> Dict[str, Any]:
        """Return service health status."""
        return {
            "service": "payment_service",
            "status": "healthy",
            "port": PORT,
            "worker_threads": WORKER_THREADS,
        }

    def run_smoke_test(self) -> bool:
        """Minimal smoke test: process one request and verify output."""
        try:
            result = self.process_request({"test": "smoke", "seed": 0})
            assert result.get("status") == "ok", f"Unexpected status: {result.get('status')}"
            assert result.get("service") == "payment_service", "Wrong service name in result"
            h = self.health_check()
            assert h.get("status") == "healthy"
            return True
        except Exception as exc:
            logger.error("Smoke test failed: %s", exc)
            return False


# ── Module-level smoke test (called by grader) ───────────────────────────────

def run_smoke_test() -> bool:
    svc = PaymentService()
    return svc.run_smoke_test()


if __name__ == "__main__":
    logger.info("Starting payment_service on port %d", PORT)
    ok = run_smoke_test()
    logger.info("Smoke test: %s", "PASS" if ok else "FAIL")
    import sys; sys.exit(0 if ok else 1)
