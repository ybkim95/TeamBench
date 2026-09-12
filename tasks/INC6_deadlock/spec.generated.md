# INC6: Distributed Deadlock — Planner Specification

## Incident Summary

**Incident ID**: INC-DL-0000
**Severity**: P1 (services intermittently hang, requiring manual restart)
**Domain**: e-commerce order processing
**Status**: Active — deadlock reproducible under concurrent load

Multiple services in the e-commerce order processing are intermittently hanging.
Restarting one service temporarily resolves the hang, but it recurs.
Thread dump analysis has identified the root cause.

---

## Lock Inventory

All shared locks in the system:

- `lock_inventory`: protects the global inventory counter
- `lock_payment`: protects the payment ledger

**Canonical lock acquisition order** (must be respected system-wide):

> **lock_inventory** MUST always be acquired before **lock_payment**

This ordering is the agreed protocol. Any service that deviates creates
a potential circular wait.

---

## Root Cause: Circular Lock Dependency

**Deadlock pair**:
- `inventory_service` acquires **lock_payment** then **lock_inventory** (WRONG ORDER)
- `payment_service` acquires **lock_inventory** then **lock_payment** (correct order)

**Circular wait**:

```
inventory_service:  holds lock_payment, waits for lock_inventory
payment_service:   holds lock_inventory, waits for lock_payment
              ^^^^^^^^ DEADLOCK ^^^^^^^^
```

**Fix**: Change `inventory_service.process_request()` to acquire `lock_inventory` first,
then `lock_payment`. Do NOT change `payment_service` — it already uses the correct order.

---

## Thread Dump Analysis

The provided `thread_dump.txt` contains three threads:

| Thread | Service | State | Holds | Waiting |
|--------|---------|-------|-------|---------|
| worker-A | `inventory_service` | BLOCKED | `lock_payment` | `lock_inventory` |
| worker-B | `payment_service` | BLOCKED | `lock_inventory` | `lock_payment` |
| poller (red herring) | `inventory_service` | HIGH-CPU POLLER (not deadlocked) | *none* | *nothing* |

**Critical distinction**: The third thread (`HIGH-CPU POLLER (not deadlocked)`) is a **red herring**.
It is CPU-bound or sleeping and holds NO locks. It is NOT part of the deadlock.
Do not remove or modify the red herring code — it is intentional production logic.

### Red Herring Details

`busy_wait_cpu`: A busy-wait polling loop that consumes 100% CPU on one thread. It appears in thread dumps as a tight loop and looks alarming, but it is intentional back-pressure logic and NOT the deadlock.

---

## Fix Requirements

1. **Open** `inventory_service.py` and locate `process_request()`.
2. **Swap** the lock acquisition order: acquire `lock_inventory` first, then `lock_payment`.
3. **Do NOT touch** `payment_service.py` — it is already correct.
4. **Preserve** the red herring code in `inventory_service.py` exactly as-is.
5. **Verify** with `python3 deadlock_sim.py --fixed` (must exit 0).
6. **Verify** with `python3 check_fix.py` (all checks must pass).
7. **Verify** both `python3 inventory_service.py` and `python3 payment_service.py` exit 0.

---

## Constraints

- Both service files must remain syntactically valid Python.
- Both smoke tests must pass (exit 0).
- The red herring code must remain present in `inventory_service.py`.
- No new deadlock may be introduced.
- Fix must address root cause; adding lock timeouts alone is insufficient.
- Do not rename locks or change their scope.

---

## Verification Checklist (for Verifier)

- [ ] `inventory_service.py` parses without syntax errors
- [ ] `payment_service.py` parses without syntax errors
- [ ] `python3 inventory_service.py` exits 0 (smoke test)
- [ ] `python3 payment_service.py` exits 0 (smoke test)
- [ ] `inventory_service.process_request()` acquires `lock_inventory` before `lock_payment`
- [ ] Red herring code present in `inventory_service.py`
- [ ] `python3 deadlock_sim.py --fixed` exits 0
- [ ] `python3 check_fix.py` reports all checks passed
- [ ] `attestation.json` has `verdict = "pass"`
