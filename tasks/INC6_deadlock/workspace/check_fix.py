"""
check_fix.py — Automated fix validator for INC6: Distributed Deadlock.

Checks:
  1. Both service files parse without syntax errors
  2. Smoke tests pass for both services
  3. Lock ordering is fixed (no circular dependency)
  4. Red herring code still present
  5. deadlock_sim.py --fixed exits 0

Usage:
    python3 check_fix.py

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
"""
import ast
import subprocess
import sys

CHECKS_PASSED = 0
CHECKS_TOTAL = 0
FAILURES = []


def check(name: str, fn) -> bool:
    global CHECKS_PASSED, CHECKS_TOTAL
    CHECKS_TOTAL += 1
    try:
        ok = fn()
        if ok:
            CHECKS_PASSED += 1
            return True
        else:
            FAILURES.append(name)
            return False
    except Exception as exc:
        print(f"  ERROR in check {name}: {exc}")
        FAILURES.append(name)
        return False


def check_syntax_both() -> bool:
    """Both service files must parse without syntax errors."""
    for fname in ["inventory_service.py", "payment_service.py"]:
        try:
            with open(fname, "r") as f:
                src = f.read()
            ast.parse(src)
            print(f"PASS: {fname} parses OK")
        except (FileNotFoundError, SyntaxError) as e:
            print(f"FAIL: {fname}: {e}")
            return False
    return True


def check_smoke_both() -> bool:
    """Both services must pass their smoke tests."""
    for fname in ["inventory_service.py", "payment_service.py"]:
        result = subprocess.run(
            [sys.executable, fname],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            print(f"FAIL: {fname} smoke test failed (exit {result.returncode})")
            print(f"  stderr: {result.stderr[:200]}")
            return False
        print(f"PASS: {fname} smoke test passed")
    return True


def check_lock_ordering_fixed() -> bool:
    """
    Verify that inventory_service.py now acquires lock_inventory before lock_payment
    (same order as payment_service.py).

    We check that in process_request(), the first `with lock_inventory` appears
    before the first `with lock_payment`.
    """
    with open("inventory_service.py", "r") as f:
        src = f.read()

    lines = src.splitlines()
    first_a = None
    first_b = None
    in_process = False
    for i, line in enumerate(lines):
        if "def process_request" in line:
            in_process = True
        if in_process:
            if first_a is None and "with lock_inventory" in line:
                first_a = i
            if first_b is None and "with lock_payment" in line:
                first_b = i
        # Stop at next top-level def
        if in_process and i > 0 and line.startswith("    def ") and "process_request" not in line:
            break

    if first_a is None or first_b is None:
        print(f"FAIL: Could not locate both lock acquires in process_request()")
        return False
    if first_a < first_b:
        print(f"PASS: Lock ordering correct — lock_inventory (line {first_a+1}) before lock_payment (line {first_b+1})")
        return True
    else:
        print(f"FAIL: Lock ordering still wrong — lock_payment (line {first_b+1}) before lock_inventory (line {first_a+1})")
        return False


def check_red_herring_present() -> bool:
    """Red herring code must still be present in inventory_service.py."""
    with open("inventory_service.py", "r") as f:
        src = f.read()
    marker = "_poll_queue"
    if marker in src:
        print(f"PASS: Red herring marker '{marker}' present")
        return True
    print(f"FAIL: Red herring code removed (marker '{marker}' missing)")
    return False


def check_sim_fixed() -> bool:
    """deadlock_sim.py --fixed must exit 0 (no deadlock)."""
    result = subprocess.run(
        [sys.executable, "deadlock_sim.py", "--fixed"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        print("PASS: deadlock_sim.py --fixed exits 0")
        return True
    print(f"FAIL: deadlock_sim.py --fixed exited {result.returncode}: {result.stdout[:200]}")
    return False


def main():
    print("=" * 60)
    print("INC6 Fix Checker — Distributed Deadlock Validation")
    print(f"Scenario: inventory_payment (seed=0)")
    print("=" * 60)
    print()

    check("syntax_both",          check_syntax_both)
    check("smoke_both",           check_smoke_both)
    check("lock_ordering_fixed",  check_lock_ordering_fixed)
    check("red_herring_present",  check_red_herring_present)
    check("sim_fixed",            check_sim_fixed)

    print()
    print(f"Results: {CHECKS_PASSED}/{CHECKS_TOTAL} checks passed")
    if FAILURES:
        print(f"Failed: {', '.join(FAILURES)}")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
