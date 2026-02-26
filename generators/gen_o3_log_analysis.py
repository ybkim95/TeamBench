"""
Parameterized generator for O3: Log Analysis + Root Cause Fix.

Each seed produces:
  - Different bug type: connection_pool_exhaustion, deadlock, cache_stampede,
    race_condition, config_drift
  - Different service type: microservice_api, batch_processor, event_handler
  - Different log volume: 500-2000 lines with signal buried in noise
  - Different port, service name, and threshold values

Workspace:
  - logs/service.log   — structured JSON logs (timestamp, level, service, msg, trace_id)
  - src/server.py      — Python service with the actual bug embedded
  - config/service.yaml — service configuration

TNI Pattern A (Hidden Constraints):
  - spec.md has the error taxonomy, the known root cause pattern, and fix procedure
  - brief.md only says "Production service is experiencing intermittent failures.
    Analyze the logs and fix the issue."
  - Without the error taxonomy, the Executor sees thousands of log lines with no
    clear signal; the Planner's taxonomy maps error codes to subsystems and patterns.
"""
from __future__ import annotations

import json
import math
import textwrap
from datetime import datetime, timedelta, timezone

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Parameterisation pools ────────────────────────────────────────────────────

BUG_TYPES = [
    "connection_pool_exhaustion",
    "deadlock",
    "cache_stampede",
    "race_condition",
    "config_drift",
]

SERVICE_TYPES = [
    "microservice_api",
    "batch_processor",
    "event_handler",
]

PORT_POOL = [8081, 8082, 8083, 8084, 8085, 8088, 8090, 8091, 8443, 9000, 9001, 9090]

SERVICE_NAME_POOLS = {
    "microservice_api":  ["order-service", "payment-service", "user-service", "catalog-service", "auth-service"],
    "batch_processor":   ["report-worker", "etl-runner", "sync-job", "batch-ingestor", "data-exporter"],
    "event_handler":     ["event-dispatcher", "webhook-consumer", "queue-worker", "stream-processor", "notifier"],
}

# Log noise message templates (realistic but not signal-bearing)
NOISE_MESSAGES = [
    ("INFO",  "Request processed successfully"),
    ("INFO",  "Cache hit for key {key}"),
    ("INFO",  "Scheduled task started"),
    ("INFO",  "Connection established to downstream"),
    ("INFO",  "Response sent in {ms}ms"),
    ("INFO",  "Health check passed"),
    ("INFO",  "Config loaded from disk"),
    ("DEBUG", "Entering request handler"),
    ("DEBUG", "Query executed in {ms}ms"),
    ("DEBUG", "Serialising response payload"),
    ("DEBUG", "Token validation succeeded"),
    ("WARN",  "Slow query detected ({ms}ms)"),
    ("WARN",  "Retry attempt {n} for upstream call"),
    ("WARN",  "Disk usage at {pct}%"),
]

# ── Bug-specific error taxonomy (lives in spec.md, not brief.md) ─────────────

BUG_TAXONOMY = {
    "connection_pool_exhaustion": {
        "error_codes": ["ERR-4001", "TIMEOUT-DB"],
        "pattern": "ERR-4001 followed by TIMEOUT-DB within 5s on the same trace_id",
        "subsystem": "database_pool",
        "fix_description": "Increase max_connections in config/service.yaml and add pool recycling",
        "buggy_config_key": "max_connections",
        "buggy_config_value": 2,
        "correct_config_value": 20,
        "signal_error_a": "ERR-4001",
        "signal_error_b": "TIMEOUT-DB",
        "signal_label": "connection pool exhausted",
        "root_cause": "Database connection pool is too small (max_connections=2); under load all connections are consumed, subsequent requests time out waiting for a free slot.",
        "fix_file": "config/service.yaml",
        "fix_field": "max_connections",
    },
    "deadlock": {
        "error_codes": ["ERR-5002", "LOCK-WAIT"],
        "pattern": "ERR-5002 followed by LOCK-WAIT on the same trace_id, recurring every 30-60s",
        "subsystem": "transaction_manager",
        "fix_description": "Fix lock acquisition order in src/server.py to prevent circular waits",
        "buggy_config_key": None,
        "buggy_config_value": None,
        "correct_config_value": None,
        "signal_error_a": "ERR-5002",
        "signal_error_b": "LOCK-WAIT",
        "signal_label": "deadlock detected",
        "root_cause": "Transaction handler acquires locks in reverse order (resource_b before resource_a) creating a circular wait when two requests run concurrently.",
        "fix_file": "src/server.py",
        "fix_field": "lock_order",
    },
    "cache_stampede": {
        "error_codes": ["ERR-6003", "CACHE-MISS"],
        "pattern": "Burst of CACHE-MISS events within 1s window followed by ERR-6003 (upstream overload)",
        "subsystem": "cache_layer",
        "fix_description": "Enable cache locking / probabilistic early expiry in config/service.yaml",
        "buggy_config_key": "cache_lock_enabled",
        "buggy_config_value": False,
        "correct_config_value": True,
        "signal_error_a": "ERR-6003",
        "signal_error_b": "CACHE-MISS",
        "signal_label": "cache stampede",
        "root_cause": "Cache locking is disabled; when the cache entry expires all concurrent requests simultaneously query the upstream, overloading it (ERR-6003).",
        "fix_file": "config/service.yaml",
        "fix_field": "cache_lock_enabled",
    },
    "race_condition": {
        "error_codes": ["ERR-7004", "STATE-CORRUPT"],
        "pattern": "ERR-7004 with STATE-CORRUPT on different trace_ids within 100ms of each other, affecting shared counter",
        "subsystem": "state_manager",
        "fix_description": "Add threading.Lock() around shared counter mutations in src/server.py",
        "buggy_config_key": None,
        "buggy_config_value": None,
        "correct_config_value": None,
        "signal_error_a": "ERR-7004",
        "signal_error_b": "STATE-CORRUPT",
        "signal_label": "race condition on shared state",
        "root_cause": "Shared request counter is incremented without a lock; concurrent threads read-modify-write simultaneously producing duplicate IDs and corrupted state.",
        "fix_file": "src/server.py",
        "fix_field": "counter_lock",
    },
    "config_drift": {
        "error_codes": ["ERR-8005", "CFG-MISMATCH"],
        "pattern": "CFG-MISMATCH at startup followed by ERR-8005 on every request; mismatch is in rate_limit_rps field",
        "subsystem": "config_validator",
        "fix_description": "Set rate_limit_rps to the correct value in config/service.yaml (must be >= 100)",
        "buggy_config_key": "rate_limit_rps",
        "buggy_config_value": 5,
        "correct_config_value": 100,
        "signal_error_a": "ERR-8005",
        "signal_error_b": "CFG-MISMATCH",
        "signal_label": "config drift causing request rejection",
        "root_cause": "rate_limit_rps is set to 5 (drifted from the required minimum of 100); every request is rejected as over-limit once the service starts.",
        "fix_file": "config/service.yaml",
        "fix_field": "rate_limit_rps",
    },
}


class Generator(TaskGenerator):
    task_id = "O3_log_analysis"
    domain = "operations"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        bug_type    = rng.choice(BUG_TYPES)
        svc_type    = rng.choice(SERVICE_TYPES)
        port        = rng.choice(PORT_POOL)
        svc_name    = rng.choice(SERVICE_NAME_POOLS[svc_type])
        log_volume  = rng.randint(500, 2000)

        tax = BUG_TAXONOMY[bug_type]

        # Generate workspace files
        log_content    = self._generate_logs(rng, seed, log_volume, svc_name, bug_type, tax)
        server_py      = self._generate_server(port, svc_name, bug_type, tax)
        service_yaml   = self._generate_config(bug_type, tax, rng)

        workspace_files = {
            "logs/service.log":    log_content,
            "src/server.py":       server_py,
            "config/service.yaml": service_yaml,
        }

        expected = {
            "bug_type":               bug_type,
            "service_type":           svc_type,
            "service_name":           svc_name,
            "port":                   port,
            "log_volume":             log_volume,
            "root_cause":             tax["root_cause"],
            "fix_file":               tax["fix_file"],
            "fix_field":              tax["fix_field"],
            "fix_description":        tax["fix_description"],
            "signal_error_a":         tax["signal_error_a"],
            "signal_error_b":         tax["signal_error_b"],
            "subsystem":              tax["subsystem"],
            "buggy_config_key":       tax["buggy_config_key"],
            "buggy_config_value":     tax["buggy_config_value"],
            "correct_config_value":   tax["correct_config_value"],
        }

        spec_md  = self._generate_spec(port, svc_name, bug_type, tax)
        brief_md = self._generate_brief(svc_name)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── Log generation ────────────────────────────────────────────────────────

    def _ts(self, base: datetime, offset_s: float) -> str:
        t = base + timedelta(seconds=offset_s)
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"

    def _trace(self, rng: SeededRandom, seed: int, idx: int) -> str:
        """Deterministic trace ID."""
        import hashlib
        h = hashlib.md5(f"{seed}:{idx}".encode()).hexdigest()
        return h[:8] + "-" + h[8:12] + "-" + h[12:16]

    def _generate_logs(
        self,
        rng: SeededRandom,
        seed: int,
        volume: int,
        svc_name: str,
        bug_type: str,
        tax: dict,
    ) -> str:
        base = datetime(2024, 3, 15, 9, 0, 0, tzinfo=timezone.utc)
        signal_error_a = tax["signal_error_a"]
        signal_error_b = tax["signal_error_b"]
        signal_label   = tax["signal_label"]

        # Always inject at least 15 signal pairs so the minimum assertion holds
        signal_count = rng.randint(15, 25)
        total_span_s = float(volume)  # 1 second per log line on average

        # --- Build noise entries (volume lines) --------------------------------
        # Each entry is (offset_seconds, json_string)
        entries: list[tuple[float, str]] = []
        offset = 0.0
        for i in range(volume):
            offset += rng.uniform(0.1, 1.2)
            level, tmpl = rng.choice(NOISE_MESSAGES)
            msg = tmpl.format(
                key=f"key_{rng.randint(1, 9999)}",
                ms=rng.randint(1, 350),
                n=rng.randint(1, 3),
                pct=rng.randint(40, 85),
            )
            trace_id = self._trace(rng, seed, i)
            entry = {
                "timestamp": self._ts(base, offset),
                "level": level,
                "service": svc_name,
                "message": msg,
                "trace_id": trace_id,
            }
            entries.append((offset, json.dumps(entry)))

        # --- Inject signal pairs at scattered positions -----------------------
        # Space them across 10%-90% of the total span to avoid clustering
        span_lo = total_span_s * 0.10
        span_hi = total_span_s * 0.90
        step = (span_hi - span_lo) / signal_count
        for k in range(signal_count):
            # jitter each pair position slightly for realism
            jitter = rng.uniform(-step * 0.3, step * 0.3)
            sig_offset = span_lo + k * step + jitter
            sig_offset = max(span_lo, min(span_hi, sig_offset))

            trace_id = self._trace(rng, seed, 10000 + k)

            entry_a = {
                "timestamp": self._ts(base, sig_offset),
                "level": "ERROR",
                "service": svc_name,
                "message": f"{signal_error_a}: {signal_label} detected",
                "trace_id": trace_id,
                "code": signal_error_a,
            }
            entries.append((sig_offset, json.dumps(entry_a)))

            gap = rng.uniform(1.0, 4.0)
            entry_b = {
                "timestamp": self._ts(base, sig_offset + gap),
                "level": "ERROR",
                "service": svc_name,
                "message": f"{signal_error_b}: follow-on failure after {signal_error_a}",
                "trace_id": trace_id,
                "code": signal_error_b,
            }
            entries.append((sig_offset + gap, json.dumps(entry_b)))

        # Sort all entries chronologically
        entries.sort(key=lambda x: x[0])
        return "\n".join(line for _, line in entries) + "\n"

    # ── Server generation ─────────────────────────────────────────────────────

    def _generate_server(self, port: int, svc_name: str, bug_type: str, tax: dict) -> str:
        """Generate src/server.py with the bug embedded."""

        if bug_type == "connection_pool_exhaustion":
            return self._server_conn_pool(port, svc_name, tax)
        elif bug_type == "deadlock":
            return self._server_deadlock(port, svc_name)
        elif bug_type == "cache_stampede":
            return self._server_cache_stampede(port, svc_name)
        elif bug_type == "race_condition":
            return self._server_race_condition(port, svc_name)
        else:  # config_drift
            return self._server_config_drift(port, svc_name, tax)

    def _server_conn_pool(self, port: int, svc_name: str, tax: dict) -> str:
        max_conn = tax["buggy_config_value"]
        return f'''\
"""
{svc_name} — microservice API server.

Bug: database connection pool is undersized; exhausted under moderate load.
The pool limit is read from config/service.yaml (max_connections).
"""
import json
import queue
import threading
import time
import yaml
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_PATH = "config/service.yaml"
_pool: queue.Queue | None = None
_pool_lock = threading.Lock()


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def get_pool() -> queue.Queue:
    global _pool
    with _pool_lock:
        if _pool is None:
            cfg = load_config()
            # BUG: reads max_connections from config but default is too small
            size = cfg.get("max_connections", {max_conn})
            _pool = queue.Queue(maxsize=size)
            for i in range(size):
                _pool.put(f"conn-{{i}}")
    return _pool


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass  # suppress default access log

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({{"status": "ok"}}))
            return
        if self.path == "/api/process":
            pool = get_pool()
            try:
                conn = pool.get(timeout=5)
            except queue.Empty:
                self._send(503, json.dumps({{"error": "ERR-4001", "detail": "pool exhausted"}}))
                return
            try:
                time.sleep(0.05)  # simulate DB work
                self._send(200, json.dumps({{"result": "ok", "conn": conn}}))
            finally:
                pool.put(conn)
            return
        self._send(404, json.dumps({{"error": "not_found"}}))


def main():
    server = HTTPServer(("127.0.0.1", {port}), Handler)
    print("{svc_name} listening on 127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    def _server_deadlock(self, port: int, svc_name: str) -> str:
        return f'''\
"""
{svc_name} — batch processor.

Bug: lock acquisition order is reversed between two code paths,
causing a deadlock when two threads run concurrently.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

lock_a = threading.Lock()
lock_b = threading.Lock()


def process_order(order_id: int) -> dict:
    # BUG: acquires lock_b before lock_a — reversed from process_payment below
    with lock_b:
        time.sleep(0.01)
        with lock_a:
            return {{"order_id": order_id, "status": "processed"}}


def process_payment(payment_id: int) -> dict:
    with lock_a:
        time.sleep(0.01)
        with lock_b:
            return {{"payment_id": payment_id, "status": "paid"}}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({{"status": "ok"}}))
            return
        if self.path.startswith("/api/order"):
            result = process_order(42)
            self._send(200, json.dumps(result))
            return
        if self.path.startswith("/api/payment"):
            result = process_payment(99)
            self._send(200, json.dumps(result))
            return
        self._send(404, json.dumps({{"error": "not_found"}}))


def main():
    server = HTTPServer(("127.0.0.1", {port}), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    def _server_cache_stampede(self, port: int, svc_name: str) -> str:
        return f'''\
"""
{svc_name} — event handler.

Bug: cache locking is disabled (cache_lock_enabled: false in config),
so on cache expiry all concurrent requests hit the upstream simultaneously.
"""
import json
import threading
import time
import yaml
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_PATH = "config/service.yaml"
_cache: dict = {{}}
_cache_lock = threading.Lock()


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def get_cached(key: str) -> str | None:
    cfg = load_config()
    # BUG: cache_lock_enabled is false — no mutex, stampede possible
    lock_enabled = cfg.get("cache_lock_enabled", False)
    if not lock_enabled:
        return _cache.get(key)
    with _cache_lock:
        return _cache.get(key)


def set_cached(key: str, value: str) -> None:
    cfg = load_config()
    lock_enabled = cfg.get("cache_lock_enabled", False)
    if not lock_enabled:
        _cache[key] = value
        return
    with _cache_lock:
        _cache[key] = value


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({{"status": "ok"}}))
            return
        if self.path.startswith("/api/resource"):
            key = self.path.split("/")[-1] or "default"
            value = get_cached(key)
            if value is None:
                time.sleep(0.05)  # simulate upstream fetch
                value = f"data-{{key}}"
                set_cached(key, value)
            self._send(200, json.dumps({{"key": key, "value": value}}))
            return
        self._send(404, json.dumps({{"error": "not_found"}}))


def main():
    server = HTTPServer(("127.0.0.1", {port}), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    def _server_race_condition(self, port: int, svc_name: str) -> str:
        return f'''\
"""
{svc_name} — microservice API.

Bug: shared request counter is mutated without a lock, causing duplicate
IDs and corrupted state under concurrent load.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# BUG: no lock around shared counter
_counter = 0


def next_request_id() -> int:
    global _counter
    # BUG: read-modify-write without synchronisation
    current = _counter
    _counter = current + 1
    return _counter


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({{"status": "ok"}}))
            return
        if self.path == "/api/job":
            req_id = next_request_id()
            self._send(200, json.dumps({{"request_id": req_id, "status": "accepted"}}))
            return
        self._send(404, json.dumps({{"error": "not_found"}}))


def main():
    server = HTTPServer(("127.0.0.1", {port}), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    def _server_config_drift(self, port: int, svc_name: str, tax: dict) -> str:
        bad_rps = tax["buggy_config_value"]
        good_rps = tax["correct_config_value"]
        return f'''\
"""
{svc_name} — API gateway.

Bug: rate_limit_rps in config/service.yaml has drifted to {bad_rps}
(minimum required is {good_rps}); every request is rejected as over-limit.
"""
import json
import time
import yaml
from http.server import BaseHTTPRequestHandler, HTTPServer

CONFIG_PATH = "config/service.yaml"
_last_reset = time.time()
_req_count = 0


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def is_rate_limited() -> bool:
    global _last_reset, _req_count
    cfg = load_config()
    # BUG: rate_limit_rps is {bad_rps} in config — far too low
    limit = cfg.get("rate_limit_rps", {bad_rps})
    now = time.time()
    if now - _last_reset >= 1.0:
        _req_count = 0
        _last_reset = now
    _req_count += 1
    return _req_count > limit


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            self._send(200, json.dumps({{"status": "ok"}}))
            return
        if self.path == "/api/data":
            if is_rate_limited():
                self._send(429, json.dumps({{"error": "ERR-8005", "detail": "rate limit exceeded"}}))
                return
            self._send(200, json.dumps({{"data": "ok"}}))
            return
        self._send(404, json.dumps({{"error": "not_found"}}))


def main():
    server = HTTPServer(("127.0.0.1", {port}), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
'''

    # ── Config generation ─────────────────────────────────────────────────────

    def _generate_config(self, bug_type: str, tax: dict, rng: SeededRandom) -> str:
        """Generate config/service.yaml with the bug-specific misconfiguration."""
        timeout  = rng.randint(10, 60)
        workers  = rng.randint(2, 8)

        if bug_type == "connection_pool_exhaustion":
            return textwrap.dedent(f"""\
                # service configuration
                max_connections: {tax['buggy_config_value']}   # BUG: too small; must be >= 20
                request_timeout_sec: {timeout}
                worker_threads: {workers}
                log_level: INFO
            """)
        elif bug_type == "deadlock":
            return textwrap.dedent(f"""\
                # service configuration
                request_timeout_sec: {timeout}
                worker_threads: {workers}
                log_level: INFO
                # Note: lock order must be: lock_a -> lock_b in all code paths
            """)
        elif bug_type == "cache_stampede":
            return textwrap.dedent(f"""\
                # service configuration
                cache_lock_enabled: false   # BUG: must be true to prevent stampede
                cache_ttl_sec: 30
                request_timeout_sec: {timeout}
                worker_threads: {workers}
                log_level: INFO
            """)
        elif bug_type == "race_condition":
            return textwrap.dedent(f"""\
                # service configuration
                request_timeout_sec: {timeout}
                worker_threads: {workers}
                log_level: INFO
                # Note: all shared state must be protected by threading.Lock()
            """)
        else:  # config_drift
            return textwrap.dedent(f"""\
                # service configuration
                rate_limit_rps: {tax['buggy_config_value']}   # BUG: drifted; must be >= {tax['correct_config_value']}
                request_timeout_sec: {timeout}
                worker_threads: {workers}
                log_level: INFO
            """)

    # ── Spec / brief ──────────────────────────────────────────────────────────

    def _generate_spec(self, port: int, svc_name: str, bug_type: str, tax: dict) -> str:
        ea = tax["signal_error_a"]
        eb = tax["signal_error_b"]
        pattern = tax["pattern"]
        subsystem = tax["subsystem"]
        root_cause = tax["root_cause"]
        fix_desc = tax["fix_description"]
        fix_file = tax["fix_file"]

        taxonomy_rows = "\n".join(
            f"| {v['signal_error_a']} | {v['signal_error_b']} | {v['subsystem']} | {k.replace('_',' ')} |"
            for k, v in BUG_TAXONOMY.items()
        )

        return f"""\
# O3: Log Analysis + Root Cause Fix

## Goal

Identify the root cause of intermittent production failures in `{svc_name}` by
analysing structured logs, then apply the minimal correct fix so the service
operates without errors.

## Error Code Taxonomy

Use this table to interpret error codes in `logs/service.log`:

| Primary Code | Secondary Code | Subsystem | Pattern Name |
|---|---|---|---|
{taxonomy_rows}

## Known Root Cause Patterns

| Pattern | Signature |
|---|---|
| connection pool exhaustion | ERR-4001 followed by TIMEOUT-DB within 5s on the same trace_id |
| deadlock | ERR-5002 followed by LOCK-WAIT on the same trace_id, recurring every 30-60s |
| cache stampede | Burst of CACHE-MISS events within 1s window followed by ERR-6003 |
| race condition | ERR-7004 with STATE-CORRUPT on different trace_ids within 100ms of each other |
| config drift | CFG-MISMATCH at startup followed by ERR-8005 on every request |

## Active Incident

- **Service**: `{svc_name}` (port `{port}`)
- **Detected pattern**: `{pattern}`
- **Affected subsystem**: `{subsystem}`
- **Root cause**: {root_cause}

## Fix Procedure

1. Confirm the pattern by grepping `logs/service.log` for `{ea}` and `{eb}` co-occurring on the same `trace_id`.
2. {fix_desc}.
3. File to edit: `{fix_file}`.
4. Verify: `GET /health` returns HTTP 200 and `GET` the primary endpoint no longer returns `{ea}`.

## Hard Requirements

1. `python src/server.py` must start and serve on `127.0.0.1:{port}`.
2. `GET /health` must return HTTP 200 with `{{"status":"ok"}}`.
3. The primary API endpoint must return HTTP 200 (not 4xx/5xx) after the fix.
4. The fix must be minimal — change only what is necessary to address the root cause.
5. Write a one-paragraph summary to `submission/root_cause.txt` identifying:
   - The error codes observed
   - The subsystem affected
   - The root cause in plain English
   - What file/field was changed and how

## Deliverables

- Fixed `{fix_file}` (or `src/server.py` for code-level bugs).
- `submission/root_cause.txt` — log analysis summary.
- Service must start cleanly and pass `/health` check.
"""

    def _generate_brief(self, svc_name: str) -> str:
        return f"""\
# O3: Log Analysis (Brief)

Production service `{svc_name}` is experiencing intermittent failures.
Analyze the logs in `logs/service.log` and fix the issue.

The Planner has the diagnostic guide and root cause patterns.
Write your findings to `submission/root_cause.txt`.
"""
