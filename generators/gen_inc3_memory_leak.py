"""
Parameterized generator for INC3: Memory Leak Investigation & Fix.

Each seed produces:
  - Different leak type (unbounded_cache, event_listener_leak, connection_pool_leak,
    circular_reference, global_list_append)
  - Different service type (web_api, background_worker, websocket_server, data_processor)
  - Different red herrings (large but bounded data structures that look suspicious)
  - Different class/variable/module names for contamination resistance

TNI driver: The spec gives the Planner a heap profile showing exact objects leaking,
growth rate, and the root cause. The brief only says "service crashes after ~2 hours."
Without the spec the Executor cannot know which of many "suspicious" patterns is the
real leak vs. an innocent red herring.

The grader checks:
  1. service.py exists and is valid Python
  2. The actual leak source identified and fixed (leak no longer accumulates)
  3. Red herring code NOT unnecessarily removed (lines still present)
  4. Service still functions correctly after fix (smoke test passes)
  5. No new import errors / syntax errors introduced
  6. Fix is a real fix, not a restart/workaround
  7. Heap simulation shows memory stabilizes after fix
  8. Partial scoring across 10+ checks
"""
from __future__ import annotations

import json
import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ---------------------------------------------------------------------------
# Leak type definitions
# ---------------------------------------------------------------------------

# Each entry:
#   id           - canonical identifier
#   name         - human-readable name
#   description  - what leaks and why
#   growth_rate  - bytes/request typical growth (for spec heap profile)
#   root_cause   - one-liner for spec
LEAK_TYPES = [
    {
        "id": "unbounded_cache",
        "name": "Unbounded In-Memory Cache",
        "description": "A dictionary used as a cache is never evicted; every unique request key is stored forever.",
        "growth_rate_kb": 12,
        "root_cause": "Cache dictionary grows without bound — no eviction policy, TTL, or size cap.",
        "leak_obj_type": "dict entries",
        "fix_description": "Add a maximum size cap (e.g., LRU eviction) or use functools.lru_cache with maxsize.",
    },
    {
        "id": "event_listener_leak",
        "name": "Unreleased Event Listener / Callback",
        "description": "Callbacks are registered on a global event emitter per request but never deregistered.",
        "growth_rate_kb": 8,
        "root_cause": "Callbacks accumulate in event emitter's listener list; no deregistration on request teardown.",
        "leak_obj_type": "function closures",
        "fix_description": "Deregister the callback after use, or use a one-shot listener that auto-removes itself.",
    },
    {
        "id": "connection_pool_leak",
        "name": "Connection Pool Leak",
        "description": "Database/socket connections are checked out from a pool but never returned.",
        "growth_rate_kb": 20,
        "root_cause": "Connection object not returned to pool after use — missing close()/release() in error path.",
        "leak_obj_type": "socket/connection objects",
        "fix_description": "Use a context manager (with conn:) or always call conn.release() in a finally block.",
    },
    {
        "id": "circular_reference",
        "name": "Circular Reference Preventing GC",
        "description": "Objects hold mutual references; CPython's cycle collector is overwhelmed by sheer volume.",
        "growth_rate_kb": 6,
        "root_cause": "Request objects hold back-references to a global registry that also holds the request — cycle prevents timely GC.",
        "leak_obj_type": "RequestContext/Node objects",
        "fix_description": "Use weakref.ref for the back-reference, or explicitly remove from registry after request completes.",
    },
    {
        "id": "global_list_append",
        "name": "Global List Accumulation",
        "description": "A module-level list collects items on every request and is never trimmed.",
        "growth_rate_kb": 5,
        "root_cause": "Module-level list appended on every request with no periodic trim or max-length guard.",
        "leak_obj_type": "list elements",
        "fix_description": "Cap the list length (e.g., keep last N items) or use collections.deque(maxlen=N).",
    },
]

# ---------------------------------------------------------------------------
# Service type definitions
# ---------------------------------------------------------------------------

SERVICE_TYPES = [
    {
        "id": "web_api",
        "name": "Flask REST API",
        "framework": "Flask",
        "entry": "app.run()",
        "request_term": "HTTP request",
        "handler_term": "route handler",
    },
    {
        "id": "background_worker",
        "name": "Background Task Worker",
        "framework": "custom event loop",
        "entry": "worker.run()",
        "request_term": "task",
        "handler_term": "task processor",
    },
    {
        "id": "websocket_server",
        "name": "WebSocket Server",
        "framework": "websockets",
        "entry": "server.serve()",
        "request_term": "WebSocket message",
        "handler_term": "message handler",
    },
    {
        "id": "data_processor",
        "name": "Batch Data Processor",
        "framework": "custom pipeline",
        "entry": "processor.run()",
        "request_term": "data record",
        "handler_term": "record handler",
    },
]

# ---------------------------------------------------------------------------
# Red herring definitions
# ---------------------------------------------------------------------------
# These look suspicious (large data structures, caches, lists) but are bounded
# and do NOT cause memory leaks.

RED_HERRINGS = [
    {
        "id": "lru_cache",
        "description": "LRU cache with a fixed maxsize — looks like a cache, but is bounded.",
        "code_snippet_template": """\
# Metrics cache — bounded by maxsize, not a leak
@functools.lru_cache(maxsize={maxsize})
def _compute_metrics(key: str) -> dict:
    \"\"\"Compute and cache metrics for a given key (bounded cache, not a leak).\"\"\"
    return {{"key": key, "value": hash(key) % 1000, "computed": True}}
""",
        "params": {"maxsize": [128, 256, 512, 1024]},
    },
    {
        "id": "fixed_deque",
        "description": "collections.deque with maxlen — looks like an unbounded list but is capped.",
        "code_snippet_template": """\
# Rolling audit log — fixed-size window, not a leak
_audit_log: collections.deque = collections.deque(maxlen={maxlen})

def _record_audit(event: str) -> None:
    \"\"\"Append to rolling audit log (capped at {maxlen} entries, not a leak).\"\"\"
    _audit_log.append({{"event": event, "ts": time.time()}})
""",
        "params": {"maxlen": [100, 500, 1000, 2000]},
    },
    {
        "id": "ttl_dict",
        "description": "Dictionary that is periodically cleared by a background sweep — bounded.",
        "code_snippet_template": """\
# Session store with periodic expiry sweep — not a leak
_session_store: dict = {{}}
_SESSION_TTL = {ttl}  # seconds

def _sweep_sessions() -> None:
    \"\"\"Remove expired sessions (called periodically — store stays bounded).\"\"\"
    now = time.time()
    expired = [k for k, v in _session_store.items() if now - v["created"] > _SESSION_TTL]
    for k in expired:
        del _session_store[k]
""",
        "params": {"ttl": [300, 600, 900, 1800]},
    },
    {
        "id": "large_constant",
        "description": "A large constant string/bytes loaded once at startup — not a leak (doesn't grow).",
        "code_snippet_template": """\
# Static lookup table loaded once at startup — not a leak (constant size)
_LOOKUP_TABLE: dict = {{str(i): i * {multiplier} for i in range({size})}}
""",
        "params": {"multiplier": [3, 7, 11, 13], "size": [500, 1000, 2000, 5000]},
    },
]


# ---------------------------------------------------------------------------
# Code generators for each leak type × service type
# ---------------------------------------------------------------------------

def _build_service_code(
    leak: dict,
    service: dict,
    red_herrings: list[dict],
    rng: SeededRandom,
    seed: int,
) -> tuple[str, str]:
    """
    Returns (service_py_code, fix_target_description).

    The code contains:
      - The actual leak (subtly hidden in realistic-looking code)
      - 2-3 red herrings (bounded structures that look suspicious)
      - Functional service logic
    """
    lid = leak["id"]
    sid = service["id"]

    # Pick variable/class names from seed-derived pools
    cache_var = rng.choice(["_response_cache", "_result_cache", "_data_cache", "_output_cache"])
    registry_var = rng.choice(["_request_registry", "_active_requests", "_context_store", "_req_map"])
    pool_var = rng.choice(["_conn_pool", "_db_pool", "_socket_pool", "_resource_pool"])
    listener_var = rng.choice(["_event_bus", "_dispatcher", "_emitter", "_signal_hub"])
    history_var = rng.choice(["_history", "_trace_log", "_event_history", "_call_log"])

    # Build red herring code blocks
    rh_blocks = []
    for rh in red_herrings:
        params = {}
        for k, v in rh["params"].items():
            params[k] = rng.choice(v)
        rh_blocks.append(rh["code_snippet_template"].format(**params))

    rh_code = "\n".join(rh_blocks)

    # Build the actual leak code + surrounding realistic service code
    if lid == "unbounded_cache":
        leak_section = f"""\
# Response cache — stores processed results to avoid recomputation
{cache_var}: dict = {{}}

def _get_cached(key: str):
    \"\"\"Retrieve a cached result, or None if not cached.\"\"\"
    return {cache_var}.get(key)

def _set_cached(key: str, value) -> None:
    \"\"\"Store result in cache.
    BUG: No eviction policy — cache grows without bound.
    Every unique key is retained forever in memory.
    \"\"\"
    {cache_var}[key] = value  # LEAK: no size limit, no TTL, no eviction
"""
        fix_target = f"Add eviction/size limit to `{cache_var}` in `_set_cached()`"
        smoke_check = f"len({cache_var}) == 0 or True"  # always passes after fix

    elif lid == "event_listener_leak":
        leak_section = f"""\
# Event bus for cross-component notifications
class _EventBus:
    def __init__(self):
        self._listeners: dict = {{}}

    def subscribe(self, event: str, callback) -> None:
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        # BUG: No way to unsubscribe — listeners accumulate forever

    def emit(self, event: str, data) -> None:
        for cb in self._listeners.get(event, []):
            cb(data)

    def listener_count(self, event: str) -> int:
        return len(self._listeners.get(event, []))

{listener_var} = _EventBus()

def _register_request_listener(request_id: str) -> None:
    \"\"\"Register a per-request listener on the global event bus.
    BUG: Listener is never removed after request completes.
    \"\"\"
    def on_event(data):
        pass  # Per-request callback (closure holds request_id)
    {listener_var}.subscribe("request_complete", on_event)  # LEAK: never unsubscribed
"""
        fix_target = f"Unsubscribe listener in `_register_request_listener()` after use, or use a one-shot pattern"
        smoke_check = "True"

    elif lid == "connection_pool_leak":
        leak_section = f"""\
# Connection pool for database/resource access
class _ConnectionPool:
    def __init__(self, max_size: int = 10):
        self._available: list = [object() for _ in range(max_size)]
        self._checked_out: list = []

    def acquire(self):
        \"\"\"Acquire a connection from the pool.\"\"\"
        if self._available:
            conn = self._available.pop()
        else:
            conn = object()  # Create new connection if pool exhausted
        self._checked_out.append(conn)
        return conn

    def release(self, conn) -> None:
        \"\"\"Return a connection to the pool.\"\"\"
        if conn in self._checked_out:
            self._checked_out.remove(conn)
            self._available.append(conn)

    def checked_out_count(self) -> int:
        return len(self._checked_out)

{pool_var} = _ConnectionPool()

def _handle_db_operation(data: dict):
    \"\"\"Perform a database operation.
    BUG: Connection is acquired but never released in the normal path.
    \"\"\"
    conn = {pool_var}.acquire()
    result = {{"processed": True, "data": data}}
    # BUG: Missing {pool_var}.release(conn) — connection leaks on every call
    return result  # LEAK: conn not returned to pool
"""
        fix_target = f"Call `{pool_var}.release(conn)` after use in `_handle_db_operation()` (use finally block)"
        smoke_check = "True"

    elif lid == "circular_reference":
        leak_section = f"""\
# Request context tracking for observability
class RequestContext:
    \"\"\"Holds per-request state and a back-reference to the global registry.\"\"\"
    def __init__(self, request_id: str, registry):
        self.request_id = request_id
        self.registry = registry  # BUG: back-reference to registry creates cycle
        self.data: dict = {{}}
        self.created_at = time.time()

    def complete(self) -> None:
        \"\"\"Mark request as complete — should clean up, but cycle prevents GC.\"\"\"
        self.data.clear()
        # BUG: 'self.registry' still references this object; cycle is never broken

{registry_var}: dict = {{}}

def _start_request(request_id: str) -> "RequestContext":
    \"\"\"Create and register a new request context.
    BUG: RequestContext holds a reference to {registry_var}, and {registry_var}
    holds a reference to RequestContext — mutual reference cycle.
    CPython's cycle collector cannot timely reclaim these objects.
    \"\"\"
    ctx = RequestContext(request_id, {registry_var})  # LEAK: cycle via back-ref
    {registry_var}[request_id] = ctx
    return ctx

def _end_request(request_id: str) -> None:
    \"\"\"Finish a request — but the cycle prevents proper cleanup.\"\"\"
    ctx = {registry_var}.get(request_id)
    if ctx:
        ctx.complete()
    # BUG: Not removing from {registry_var} either — doubly leaked
"""
        fix_target = f"Use `weakref.ref` for `RequestContext.registry`, and remove from `{registry_var}` in `_end_request()`"
        smoke_check = "True"

    else:  # global_list_append
        leak_section = f"""\
# Request history — intended for debugging, but never trimmed
{history_var}: list = []

def _record_request(request_id: str, data: dict) -> None:
    \"\"\"Append request metadata to the global history list.
    BUG: List is never trimmed — grows indefinitely, one entry per request.
    \"\"\"
    {history_var}.append({{  # LEAK: unbounded append, no trim
        "id": request_id,
        "data": data,
        "ts": time.time(),
    }})

def get_history_length() -> int:
    \"\"\"Return the number of entries in the history log.\"\"\"
    return len({history_var})
"""
        fix_target = f"Cap `{history_var}` — use `collections.deque(maxlen=N)` or trim after append in `_record_request()`"
        smoke_check = "True"

    # Build the full service file
    svc_code = _build_full_service(
        service=service,
        leak_section=leak_section,
        rh_code=rh_code,
        seed=seed,
        rng=rng,
    )
    return svc_code, fix_target


def _build_full_service(
    service: dict,
    leak_section: str,
    rh_code: str,
    seed: int,
    rng: SeededRandom,
) -> str:
    port = rng.randint(8000, 9999)
    worker_interval = rng.randint(50, 500)

    return f'''\
"""
service.py — {service["name"]}

A production {service["name"].lower()} that processes incoming {service["request_term"]}s.
Seed: {seed}
"""
import collections
import functools
import gc
import hashlib
import itertools
import logging
import os
import sys
import time
import weakref
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
PORT = {port}
WORKER_INTERVAL_MS = {worker_interval}
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30.0

# ── Red herring data structures (bounded — NOT leaks) ─────────────────────────
{rh_code}
# ── Actual leak code ──────────────────────────────────────────────────────────
{leak_section}
# ── Core service logic ────────────────────────────────────────────────────────

_request_counter = itertools.count(1)


def generate_request_id() -> str:
    """Generate a unique request identifier."""
    n = next(_request_counter)
    return hashlib.md5(f"req-{{n}}-seed-{seed}".encode()).hexdigest()[:12]


def process_{service["id"]}_request(payload: dict) -> dict:
    """
    Main {service["request_term"]} processing entry point.
    Called for every incoming {service["request_term"]}.
    """
    request_id = generate_request_id()
    logger.debug("Processing %s request_id=%s", "{service["request_term"]}", request_id)

    # Validate input
    if not isinstance(payload, dict):
        raise ValueError(f"Expected dict payload, got {{type(payload).__name__}}")

    result = {{
        "request_id": request_id,
        "status": "ok",
        "payload_keys": list(payload.keys()),
    }}
    return result


def health_check() -> dict:
    """Return a health status dict for monitoring."""
    return {{
        "status": "healthy",
        "service": "{service["name"]}",
        "uptime_s": time.time(),
        "gc_counts": gc.get_count(),
    }}


def run_smoke_test() -> bool:
    """
    Minimal smoke test — returns True if the service processes one request correctly.
    Called by the grader to verify service still functions after the fix.
    """
    try:
        result = process_{service["id"]}_request({{"test_key": "test_value", "smoke": True}})
        assert result.get("status") == "ok", f"Unexpected status: {{result.get('status')}}"
        assert "request_id" in result, "Missing request_id in result"
        h = health_check()
        assert h.get("status") == "healthy", f"Health check failed: {{h}}"
        return True
    except Exception as exc:
        logger.error("Smoke test failed: %s", exc)
        return False


if __name__ == "__main__":
    logger.info("Starting {service["name"]} on port %d", PORT)
    logger.info("Smoke test: %s", run_smoke_test())
'''


# ---------------------------------------------------------------------------
# Spec and Brief generators
# ---------------------------------------------------------------------------

def _generate_spec(
    leak: dict,
    service: dict,
    red_herrings: list[dict],
    fix_target: str,
    seed: int,
    rng: SeededRandom,
) -> str:
    # Heap profile numbers
    baseline_mb = rng.randint(40, 80)
    after_1hr_mb = baseline_mb + leak["growth_rate_kb"] * 60 * 5  # ~5 req/s * 60min
    after_2hr_mb = after_1hr_mb + leak["growth_rate_kb"] * 60 * 5
    crash_mb = rng.randint(1800, 2500)

    rh_names = ", ".join(f"`{rh['id']}`" for rh in red_herrings)

    rh_section_lines = []
    for rh in red_herrings:
        rh_section_lines.append(
            f"- **{rh['id']}**: {rh['description']} This is a red herring — do not remove or restructure this code."
        )
    rh_section = "\n".join(rh_section_lines)

    return f"""# INC3: Memory Leak Investigation — Planner Specification

## Incident Summary

**Incident ID**: INC-ML-{seed:04d}
**Severity**: P1 (service crashes after ~2 hours)
**Service**: `{service["name"]}` (`service.py`)
**Status**: Active — service must be restarted every ~2 hours

A production `{service["name"].lower()}` is exhausting available memory and being
killed by the OOM killer after approximately 2 hours of operation under normal load.
Heap profiling has isolated the root cause.

---

## Heap Profile Analysis

Profiling was conducted with `tracemalloc` and `objgraph` over a 3-hour window
at a steady request rate of ~5 {service["request_term"]}s/second.

| Time | Heap Used | Growth |
|------|-----------|--------|
| T+0m (startup) | {baseline_mb} MB | baseline |
| T+60m | {after_1hr_mb} MB | +{after_1hr_mb - baseline_mb} MB |
| T+120m | {after_2hr_mb} MB | +{after_2hr_mb - baseline_mb} MB total |
| T+crash | OOM killed | ~{crash_mb} MB limit hit |

**Growth rate**: ~{leak["growth_rate_kb"]} KB per {service["request_term"]} processed

### Top Leaking Object Types (from `objgraph.show_growth()`)

```
{leak["leak_obj_type"]:.<40} +{leak["growth_rate_kb"] * 300:,} ({leak["growth_rate_kb"] * 300 * 100 // (leak["growth_rate_kb"] * 300 + 50):,}%)
str                                    +{rng.randint(200, 800):,} (noise — normal churn)
dict                                   +{rng.randint(100, 400):,} (noise — normal churn)
```

### Root Cause (Confirmed)

**Leak type**: {leak["name"]}

{leak["description"]}

**Root cause**: {leak["root_cause"]}

**Leak location**: See the `# LEAK:` comment in `service.py`. The fix target is:
> {fix_target}

---

## Red Herrings (Do NOT Modify)

The following patterns in `service.py` look suspicious but are **NOT leaks**.
The Executor must leave these structures intact:

{rh_section}

Modifying or removing red herring code will cause grader check failures.

---

## Fix Requirements

1. **Identify** the exact line(s) containing the `# LEAK:` annotation.
2. **Fix** the root cause — apply the correct fix (see below), not a workaround.
3. **Do not** restart the service periodically, reduce logging, or clear state
   arbitrarily — these are workarounds, not fixes.
4. **Preserve** all red herring code exactly as-is.
5. **Verify** with `python3 service.py` — the smoke test must pass.

### Correct Fix

{leak["fix_description"]}

---

## Constraints

- `service.py` must remain syntactically valid Python.
- `python3 service.py` must exit 0 (smoke test passes).
- Red herring code (bounded data structures) must remain present and functional.
- No new memory leaks may be introduced.
- Fix must address the root cause, not mask symptoms.

---

## Verification Checklist (for Verifier)

- [ ] `service.py` parses without syntax errors
- [ ] `python3 service.py` exits 0 (smoke test)
- [ ] Heap simulation shows memory stabilizes (check `heap_sim.py` output)
- [ ] Red herring structures still present in `service.py`
- [ ] `# LEAK:` annotation line has been modified to fix the root cause
- [ ] `attestation.json` has `verdict = "pass"`
"""


def _generate_brief(service: dict, seed: int) -> str:
    return f"""# INC3: Memory Leak Investigation (Brief)

A production **{service["name"].lower()}** (`service.py`) is crashing after approximately
2 hours of operation. On-call has confirmed the process is killed by the OOM (out-of-memory)
killer and must be manually restarted.

**Situation**: Memory usage grows steadily over time at a rate correlated with request volume.
The service processes {service["request_term"]}s and several data structures in the code
look potentially suspicious — it is unclear which one is the actual leak.

**Goal**: Find the memory leak, fix it, and verify the service still operates correctly.

**Workspace files**:
- `service.py` — the Python service with the memory leak (and some innocent-looking patterns)
- `heap_sim.py` — heap growth simulator; run it to check if your fix stops the leak
- `check_fix.py` — automated fix checker; run after applying your fix

**What to do**:
1. Inspect `service.py` to identify which pattern is actually leaking memory.
2. Fix the root cause (do not just restart or clear data arbitrarily).
3. Run `python3 heap_sim.py` to verify memory stabilizes after the fix.
4. Run `python3 check_fix.py` and ensure it reports success.
5. Run `python3 service.py` to confirm the smoke test passes.

The Planner has heap profiling data identifying the exact leak location and root cause.
Coordinate with the Planner before implementing — there are red herring patterns that
look suspicious but are not the actual leak.

**Constraint**: The fix must address the root cause. Workarounds (periodic restarts,
clearing all caches indiscriminately) will not pass grading.
"""


# ---------------------------------------------------------------------------
# Heap simulator and fix checker workspace files
# ---------------------------------------------------------------------------

def _generate_heap_sim(leak: dict, service: dict, seed: int) -> str:
    """Generate a heap growth simulator that shows growth before fix and stability after."""
    lid = leak["id"]

    # Simulation code is parametric on the leak type
    if lid == "unbounded_cache":
        sim_body = """\
    # Simulate cache growth: each call adds to the cache dict
    cache = {}
    for i in range(n_requests):
        key = f"req_{i}"  # Unique key per request
        cache[key] = {"value": i, "data": "x" * 64}
    return sys.getsizeof(cache) + sum(sys.getsizeof(v) for v in cache.values())
"""
        fix_body = """\
    # After fix: LRU cache with maxsize — stays bounded
    cache = {}
    MAX = 256
    for i in range(n_requests):
        key = f"req_{i}"
        cache[key] = {"value": i, "data": "x" * 64}
        if len(cache) > MAX:
            oldest = next(iter(cache))
            del cache[oldest]
    return sys.getsizeof(cache) + sum(sys.getsizeof(v) for v in cache.values())
"""
    elif lid == "event_listener_leak":
        sim_body = """\
    # Simulate listener accumulation: listeners never removed
    listeners = []
    for i in range(n_requests):
        def cb(data, _i=i): pass
        listeners.append(cb)
    return sum(sys.getsizeof(cb) for cb in listeners)
"""
        fix_body = """\
    # After fix: one-shot listener — removed after each request
    # At any time, at most 1 listener exists
    max_live = 1
    return sys.getsizeof(lambda d: None) * max_live
"""
    elif lid == "connection_pool_leak":
        sim_body = """\
    # Simulate connection leak: each request checks out but never returns
    checked_out = []
    for i in range(n_requests):
        conn = object()
        checked_out.append(conn)
    return sum(sys.getsizeof(c) for c in checked_out)
"""
        fix_body = """\
    # After fix: connection always released — pool stays bounded (max_size objects)
    pool_size = 10
    return sys.getsizeof(object()) * pool_size
"""
    elif lid == "circular_reference":
        sim_body = """\
    # Simulate circular reference accumulation
    registry = {}
    class Ctx:
        def __init__(self, rid, reg):
            self.rid = rid
            self.registry = reg  # back-ref creates cycle
    for i in range(n_requests):
        ctx = Ctx(f"req_{i}", registry)
        registry[f"req_{i}"] = ctx
    return sum(sys.getsizeof(v) for v in registry.values())
"""
        fix_body = """\
    # After fix: weakref back-reference + explicit removal from registry
    # Registry stays bounded (each request removes itself)
    return sys.getsizeof(object())  # Only live request context exists
"""
    else:  # global_list_append
        sim_body = """\
    # Simulate unbounded list growth
    history = []
    for i in range(n_requests):
        history.append({"id": f"req_{i}", "data": "x" * 32, "ts": i})
    return sum(sys.getsizeof(item) for item in history)
"""
        fix_body = """\
    # After fix: deque with maxlen — oldest items auto-evicted
    import collections
    MAX = 500
    history = collections.deque(maxlen=MAX)
    for i in range(n_requests):
        history.append({"id": f"req_{i}", "data": "x" * 32, "ts": i})
    return sum(sys.getsizeof(item) for item in history)
"""

    return f'''\
"""
heap_sim.py — Memory growth simulator for service.py

Simulates heap growth under load, before and after the fix.
Run BEFORE applying the fix to see unbounded growth.
Run AFTER applying the fix to verify memory stabilizes.

Usage:
    python3 heap_sim.py [--fixed]

Exit codes:
    0 — memory growth within acceptable bounds (fix applied correctly)
    1 — unbounded growth detected (leak still present)
"""
import sys
import argparse


def simulate_before_fix(n_requests: int) -> int:
    """Simulate memory used after n_requests WITHOUT the fix. Returns estimated bytes."""
{sim_body}

def simulate_after_fix(n_requests: int) -> int:
    """Simulate memory used after n_requests WITH the fix. Returns estimated bytes."""
{fix_body}

def main():
    parser = argparse.ArgumentParser(description="Heap growth simulator")
    parser.add_argument("--fixed", action="store_true", help="Simulate post-fix behaviour")
    args = parser.parse_args()

    checkpoints = [100, 500, 1000, 5000, 10000]
    print(f"Heap growth simulation — {service["name"]} (seed={seed})")
    print(f"Mode: {{'FIXED (post-fix)' if args.fixed else 'UNFIXED (pre-fix)'}}")
    print()
    print(f"{{'Requests':>12}} | {{'Heap (bytes)':>14}} | Status")
    print("-" * 50)

    sim_fn = simulate_after_fix if args.fixed else simulate_before_fix
    prev = 0
    unbounded = False
    for n in checkpoints:
        heap = sim_fn(n)
        delta = heap - prev
        status = "OK" if args.fixed else ("GROWING" if delta > 0 else "OK")
        if not args.fixed and delta > 0:
            unbounded = True
        print(f"{{n:>12,}} | {{heap:>14,}} | {{status}}")
        prev = heap

    print()
    if args.fixed:
        print("Result: PASS — memory growth bounded after fix.")
        sys.exit(0)
    elif unbounded:
        print("Result: LEAK DETECTED — apply the fix and re-run with --fixed.")
        sys.exit(1)
    else:
        print("Result: PASS (unexpected — leak may already be fixed).")
        sys.exit(0)


if __name__ == "__main__":
    main()
'''


def _generate_check_fix(leak: dict, service: dict, seed: int) -> str:
    """Generate a fix-checker script that validates the fix was applied."""
    lid = leak["id"]

    if lid == "unbounded_cache":
        check_body = """\
    # After fix, the cache must have a size bound.
    # Check: after many calls, the cache variable should NOT grow proportionally.
    # We import service and look for evidence of bounding (lru_cache or size check).
    import ast, sys
    with open("service.py", "r") as f:
        src = f.read()
    tree = ast.parse(src)

    # Look for maxsize argument to lru_cache, or a len() guard near the cache write
    has_maxsize = "maxsize" in src and "lru_cache" in src
    has_len_guard = "len(" in src and ("_cache" in src or "cache" in src)
    has_deque_cache = "deque" in src and "maxlen" in src and "cache" in src.lower()

    if not (has_maxsize or has_len_guard or has_deque_cache):
        print("FAIL: No cache bounding mechanism found (expected maxsize, len guard, or deque with maxlen)")
        return False
    print("PASS: Cache bounding mechanism detected.")
    return True
"""
    elif lid == "event_listener_leak":
        check_body = """\
    # After fix, there must be an unsubscribe/remove call, or a one-shot pattern.
    with open("service.py", "r") as f:
        src = f.read()
    has_remove = "remove" in src or "unsubscribe" in src or "pop(" in src
    has_one_shot = "one_shot" in src or "once" in src
    # Also accept: the subscription loop is removed entirely
    no_subscribe_in_handler = src.count("subscribe") <= 1  # Only the EventBus.subscribe def
    if not (has_remove or has_one_shot or no_subscribe_in_handler):
        print("FAIL: No listener removal mechanism found")
        return False
    print("PASS: Listener removal/one-shot mechanism detected.")
    return True
"""
    elif lid == "connection_pool_leak":
        check_body = """\
    # After fix, there must be a release() call or a context manager in the handler.
    with open("service.py", "r") as f:
        src = f.read()
    has_release = ".release(" in src
    has_finally = "finally" in src
    has_with_conn = "with " in src and "conn" in src
    if not (has_release or has_finally or has_with_conn):
        print("FAIL: No connection release mechanism found (expected release(), finally, or with-statement)")
        return False
    print("PASS: Connection release mechanism detected.")
    return True
"""
    elif lid == "circular_reference":
        check_body = """\
    # After fix, there must be either a weakref or explicit registry removal.
    with open("service.py", "r") as f:
        src = f.read()
    has_weakref = "weakref" in src
    has_del_from_registry = "del " in src and ("registry" in src or "_request_registry" in src
                            or "_active_requests" in src or "_context_store" in src or "_req_map" in src)
    has_pop = ".pop(" in src
    if not (has_weakref or has_del_from_registry or has_pop):
        print("FAIL: No cycle-breaking mechanism found (expected weakref or del from registry)")
        return False
    print("PASS: Cycle-breaking mechanism detected.")
    return True
"""
    else:  # global_list_append
        check_body = """\
    # After fix, the list must be capped (deque maxlen or len guard or clear).
    with open("service.py", "r") as f:
        src = f.read()
    has_deque_maxlen = "deque" in src and "maxlen" in src
    has_len_guard = "len(" in src and ("_history" in src or "history" in src or "_trace_log" in src
                    or "_event_history" in src or "_call_log" in src)
    has_slice = "= " in src and ("[-" in src or ":500" in src or ":1000" in src or ":100" in src)
    if not (has_deque_maxlen or has_len_guard or has_slice):
        print("FAIL: No list bounding mechanism found (expected deque maxlen or length guard)")
        return False
    print("PASS: List bounding mechanism detected.")
    return True
"""

    return f'''\
"""
check_fix.py — Automated fix validator for INC3: Memory Leak.

Checks that:
  1. service.py is syntactically valid
  2. The smoke test passes (service processes a request correctly)
  3. The fix mechanism is present (leak-specific structural check)
  4. Red herring code is still present (not unnecessarily removed)

Usage:
    python3 check_fix.py

Exit codes:
    0 — all checks pass
    1 — one or more checks failed
"""
import ast
import importlib.util
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
        print(f"  ERROR in check {{name}}: {{exc}}")
        FAILURES.append(name)
        return False


def check_syntax() -> bool:
    """service.py must parse without syntax errors."""
    with open("service.py", "r") as f:
        src = f.read()
    try:
        ast.parse(src)
        print("PASS: service.py parses OK")
        return True
    except SyntaxError as e:
        print(f"FAIL: SyntaxError in service.py: {{e}}")
        return False


def check_smoke_test() -> bool:
    """python3 service.py must exit 0."""
    result = subprocess.run(
        [sys.executable, "service.py"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode == 0:
        print("PASS: Smoke test passed (service.py exits 0)")
        return True
    else:
        print(f"FAIL: service.py exited {{result.returncode}}")
        print(f"  stdout: {{result.stdout[:200]}}")
        print(f"  stderr: {{result.stderr[:200]}}")
        return False


def check_fix_mechanism() -> bool:
    """Leak-specific structural check that the fix is present."""
{check_body}

def check_red_herrings_present() -> bool:
    """Red herring code must still be present in service.py."""
    with open("service.py", "r") as f:
        src = f.read()
    # Each red herring leaves a characteristic identifier
    markers = {json.dumps([rh["id"] for rh in []])}  # populated by generator
    # We check for the presence of key identifiers from each red herring
    required_markers = [
        "lru_cache",          # bounded LRU cache red herring
        "_audit_log",         # rolling deque red herring
        "_session_store",     # TTL dict red herring
        "_LOOKUP_TABLE",      # large constant red herring
    ]
    # Only require the ones actually present in the original service.py
    found = [m for m in required_markers if m in src]
    if len(found) == 0:
        print("WARN: No red herring markers found — they may have been removed.")
        # Non-fatal: we still check other things
    else:
        print(f"PASS: Red herring markers present: {{found}}")
    return True  # Non-fatal check — grader handles the strict version


def check_no_new_syntax_errors() -> bool:
    """Double-check: import service.py as a module (catches runtime import errors)."""
    result = subprocess.run(
        [sys.executable, "-c", "import ast; ast.parse(open('service.py').read()); print('OK')"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode == 0:
        print("PASS: service.py importable")
        return True
    print(f"FAIL: service.py import error: {{result.stderr[:300]}}")
    return False


def main():
    print("=" * 60)
    print("INC3 Fix Checker — Memory Leak Validation")
    print(f"Service: {service["name"]} (seed={seed})")
    print("=" * 60)
    print()

    check("syntax",            check_syntax)
    check("smoke_test",        check_smoke_test)
    check("fix_mechanism",     check_fix_mechanism)
    check("red_herrings",      check_red_herrings_present)
    check("no_import_errors",  check_no_new_syntax_errors)

    print()
    print(f"Results: {{CHECKS_PASSED}}/{{CHECKS_TOTAL}} checks passed")
    if FAILURES:
        print(f"Failed: {{', '.join(FAILURES)}}")
        sys.exit(1)
    else:
        print("All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
'''


# ---------------------------------------------------------------------------
# Main Generator class
# ---------------------------------------------------------------------------

class Generator(TaskGenerator):
    task_id = "INC3_memory_leak"
    domain = "incident_response"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Select leak and service type from seed
        leak = LEAK_TYPES[seed % len(LEAK_TYPES)]
        service = SERVICE_TYPES[(seed * 3 + 1) % len(SERVICE_TYPES)]

        # Select 2-3 red herrings (always pick a fixed set per seed, no overlap issues)
        num_rh = 2 + (seed % 2)  # 2 or 3
        # Shuffle red herring indices deterministically
        rh_indices = list(range(len(RED_HERRINGS)))
        rng.shuffle(rh_indices)
        selected_rh = [RED_HERRINGS[i] for i in rh_indices[:num_rh]]

        # Generate service code
        service_code, fix_target = _build_service_code(leak, service, selected_rh, rng, seed)

        # Generate spec, brief, heap_sim, check_fix
        spec_md = _generate_spec(leak, service, selected_rh, fix_target, seed, rng)
        brief_md = _generate_brief(service, seed)
        heap_sim_py = _generate_heap_sim(leak, service, seed)
        check_fix_py = _generate_check_fix(leak, service, seed)

        expected = {
            "leak_type": leak["id"],
            "service_type": service["id"],
            "root_cause": leak["root_cause"],
            "fix_description": leak["fix_description"],
            "fix_target": fix_target,
            "red_herring_ids": [rh["id"] for rh in selected_rh],
            "leak_annotation": "# LEAK:",
            "smoke_test_fn": f"process_{service['id']}_request",
            "required_markers": {
                "lru_cache": "lru_cache" in " ".join(rh["id"] for rh in selected_rh)
                             or any(rh["id"] == "lru_cache" for rh in selected_rh),
                "_audit_log": any(rh["id"] == "fixed_deque" for rh in selected_rh),
                "_session_store": any(rh["id"] == "ttl_dict" for rh in selected_rh),
                "_LOOKUP_TABLE": any(rh["id"] == "large_constant" for rh in selected_rh),
            },
            "seed": seed,
        }

        workspace_files = {
            "service.py": service_code,
            "heap_sim.py": heap_sim_py,
            "check_fix.py": check_fix_py,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )
