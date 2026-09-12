"""
deadlock_sim.py — Deadlock demonstration and fix verifier.

Simulates concurrent access by the two services.

Usage:
    python3 deadlock_sim.py            # Run with buggy lock order (will deadlock)
    python3 deadlock_sim.py --fixed    # Run with fixed lock order (should not deadlock)

Exit codes:
    0 — No deadlock (correct lock ordering)
    1 — Deadlock detected (incorrect lock ordering)
    2 — Timeout (presumed deadlock)
"""
import argparse
import sys
import threading
import time

# Shared locks (simulated)
lock_inventory = threading.Lock()
lock_payment = threading.Lock()

TIMEOUT = 3.0  # seconds to wait before declaring deadlock
result_a = None
result_b = None
error_a = None
error_b = None


def service_a_buggy():
    """Buggy: acquires lock_payment then lock_inventory — opposite to service_b."""
    global result_a, error_a
    try:
        with lock_payment:
            time.sleep(0.05)
            with lock_inventory:
                result_a = "done"
    except Exception as e:
        error_a = str(e)


def service_b_correct():
    """Correct order: acquires lock_inventory then lock_payment."""
    global result_b, error_b
    try:
        with lock_inventory:
            time.sleep(0.05)
            with lock_payment:
                result_b = "done"
    except Exception as e:
        error_b = str(e)


def service_a_fixed():
    """Fixed: acquires lock_inventory then lock_payment — same as service_b."""
    global result_a, error_a
    try:
        with lock_inventory:
            time.sleep(0.05)
            with lock_payment:
                result_a = "done"
    except Exception as e:
        error_a = str(e)


def main():
    global result_a, result_b
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed", action="store_true", help="Use fixed lock ordering")
    args = parser.parse_args()

    fn_a = service_a_fixed if args.fixed else service_a_buggy
    fn_b = service_b_correct

    t_a = threading.Thread(target=fn_a, name="service-a", daemon=True)
    t_b = threading.Thread(target=fn_b, name="service-b", daemon=True)

    t_a.start()
    t_b.start()

    t_a.join(timeout=TIMEOUT)
    t_b.join(timeout=TIMEOUT)

    if t_a.is_alive() or t_b.is_alive():
        print("RESULT: DEADLOCK DETECTED — threads still blocked after timeout")
        print(f"  service-a alive: {t_a.is_alive()}")
        print(f"  service-b alive: {t_b.is_alive()}")
        sys.exit(2)
    elif error_a or error_b:
        print(f"RESULT: ERROR — service_a error={error_a}, service_b error={error_b}")
        sys.exit(1)
    else:
        print(f"RESULT: OK — No deadlock. result_a={result_a}, result_b={result_b}")
        sys.exit(0)


if __name__ == "__main__":
    main()
