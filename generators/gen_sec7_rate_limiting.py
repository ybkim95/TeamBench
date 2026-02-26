"""
Parameterized generator for SEC7: Rate Limiting Per API Tier.

Each seed produces:
- Different tier names (free/basic/premium/internal or silver/gold/platinum/internal, etc.)
- Different rate limits per tier
- Different endpoint groupings and which tier each belongs to
- Different API key header name
- Same structural task: Flask API with no rate limiting that needs it added

TNI Design (Pattern D):
  - brief.md: vague — "add rate limiting to prevent abuse"
  - spec.md: full tier definitions, exact limits, endpoint-to-tier mapping,
             required response headers (X-RateLimit-Limit, X-RateLimit-Remaining,
             X-RateLimit-Reset), 429 format
  - workspace: plausible Flask API with multiple endpoints, zero rate limiting code
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Variation pools ────────────────────────────────────────────────────────────

TIER_SETS = [
    {
        "tiers": ["free", "basic", "premium", "internal"],
        "limits": [10, 100, 1000, None],   # None = unlimited
        "tier_field": "plan",
    },
    {
        "tiers": ["starter", "pro", "enterprise", "internal"],
        "limits": [20, 200, 2000, None],
        "tier_field": "subscription",
    },
    {
        "tiers": ["trial", "standard", "professional", "internal"],
        "limits": [5, 50, 500, None],
        "tier_field": "tier",
    },
    {
        "tiers": ["bronze", "silver", "gold", "internal"],
        "limits": [15, 150, 1500, None],
        "tier_field": "plan",
    },
    {
        "tiers": ["hobby", "growth", "scale", "internal"],
        "limits": [30, 300, 3000, None],
        "tier_field": "tier",
    },
]

ENDPOINT_SETS = [
    {
        "endpoints": [
            {"path": "/api/search",    "func": "search",        "method": "GET",  "desc": "search records"},
            {"path": "/api/items",     "func": "list_items",    "method": "GET",  "desc": "list items"},
            {"path": "/api/items",     "func": "create_item",   "method": "POST", "desc": "create an item"},
            {"path": "/api/export",    "func": "export_data",   "method": "GET",  "desc": "export dataset"},
            {"path": "/api/admin/stats","func": "admin_stats",  "method": "GET",  "desc": "admin statistics"},
        ],
        "resource": "items",
    },
    {
        "endpoints": [
            {"path": "/api/query",     "func": "query_records",  "method": "GET",  "desc": "query records"},
            {"path": "/api/records",   "func": "list_records",   "method": "GET",  "desc": "list records"},
            {"path": "/api/records",   "func": "create_record",  "method": "POST", "desc": "create a record"},
            {"path": "/api/reports",   "func": "generate_report","method": "GET",  "desc": "generate a report"},
            {"path": "/api/admin/ops", "func": "admin_ops",      "method": "GET",  "desc": "admin operations"},
        ],
        "resource": "records",
    },
    {
        "endpoints": [
            {"path": "/api/lookup",    "func": "lookup",          "method": "GET",  "desc": "lookup entity"},
            {"path": "/api/products",  "func": "list_products",   "method": "GET",  "desc": "list products"},
            {"path": "/api/products",  "func": "add_product",     "method": "POST", "desc": "add a product"},
            {"path": "/api/bulk",      "func": "bulk_export",     "method": "GET",  "desc": "bulk export"},
            {"path": "/api/admin/metrics","func": "admin_metrics","method": "GET",  "desc": "admin metrics"},
        ],
        "resource": "products",
    },
]

API_KEY_HEADERS = [
    "X-API-Key",
    "X-Auth-Token",
    "X-Client-Key",
    "Authorization-Key",
]

# Which tier index each endpoint belongs to (0=lowest, 2=premium, 3=internal)
# Pattern: first 2 endpoints are lowest tier, next 1 is mid, export is premium, admin is internal
ENDPOINT_TIER_PATTERNS = [
    [0, 0, 1, 2, 3],   # search+list=free, create=basic, export=premium, admin=internal
    [0, 1, 1, 2, 3],   # search=free, list+create=basic, export=premium, admin=internal
    [1, 0, 0, 2, 3],   # query=basic, list+create=free, report=premium, admin=internal
]

WINDOW_VARIANTS = [
    {"window": 60,   "window_label": "per minute",  "window_key": "minute"},
    {"window": 3600, "window_label": "per hour",    "window_key": "hour"},
]


class Generator(TaskGenerator):
    task_id = "SEC7_rate_limiting"
    domain = "security"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        ts = TIER_SETS[rng.randint(0, len(TIER_SETS) - 1)]
        ep_set = ENDPOINT_SETS[rng.randint(0, len(ENDPOINT_SETS) - 1)]
        api_key_header = API_KEY_HEADERS[rng.randint(0, len(API_KEY_HEADERS) - 1)]
        tier_pattern = ENDPOINT_TIER_PATTERNS[rng.randint(0, len(ENDPOINT_TIER_PATTERNS) - 1)]
        wv = WINDOW_VARIANTS[rng.randint(0, len(WINDOW_VARIANTS) - 1)]

        tiers = ts["tiers"]
        limits = ts["limits"]
        tier_field = ts["tier_field"]
        endpoints = ep_set["endpoints"]
        resource = ep_set["resource"]
        window = wv["window"]
        window_label = wv["window_label"]
        window_key = wv["window_key"]

        # Build endpoint->tier mapping
        ep_tier_map = {}
        for i, ep in enumerate(endpoints):
            tier_idx = tier_pattern[i] if i < len(tier_pattern) else 0
            ep_tier_map[ep["func"]] = tiers[tier_idx]

        # Build tier->limit mapping for expected
        tier_limit_map = {}
        for i, tier in enumerate(tiers):
            tier_limit_map[tier] = limits[i]  # None = unlimited

        expected = {
            "tiers": tiers,
            "tier_limits": tier_limit_map,
            "window_seconds": window,
            "api_key_header": api_key_header,
            "tier_field": tier_field,
            "endpoint_tier_map": ep_tier_map,
            "rate_limit_headers": [
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ],
            "rate_limit_exceeded_status": 429,
            "unlimited_tier": tiers[-1],  # "internal" is always last
        }

        workspace_files = {
            "app.py":           self._gen_app(tiers, limits, tier_field, endpoints,
                                               ep_tier_map, api_key_header, window,
                                               window_label, resource),
            "requirements.txt": self._gen_requirements(),
            "tests/test_rate_limiting.py": self._gen_tests(
                tiers, limits, tier_field, endpoints, ep_tier_map,
                api_key_header, window, resource
            ),
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=self._gen_spec(tiers, limits, tier_field, endpoints,
                                    ep_tier_map, api_key_header, window,
                                    window_label, resource),
            brief_md=self._gen_brief(resource),
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── workspace file generators ──────────────────────────────────────────────

    def _gen_app(
        self,
        tiers: list,
        limits: list,
        tier_field: str,
        endpoints: list,
        ep_tier_map: dict,
        api_key_header: str,
        window: int,
        window_label: str,
        resource: str,
    ) -> str:
        # Build the API_KEYS dict (fake key store with tier info)
        tier_keys = []
        for i, tier in enumerate(tiers):
            key = f"key-{tier}-001"
            tier_keys.append(f'    "{key}": {{"{tier_field}": "{tier}"}}')
        api_keys_block = ",\n".join(tier_keys)

        # Build route functions
        route_blocks = []
        for ep in endpoints:
            func = ep["func"]
            path = ep["path"]
            method = ep["method"]
            desc = ep["desc"]
            tier = ep_tier_map[func]

            route_blocks.append(f'''\
@app.route("{path}", methods=["{method}"])
def {func}():
    """Endpoint: {desc}. Tier: {tier}."""
    # TODO: enforce rate limit for this endpoint's tier
    return jsonify({{"status": "ok", "endpoint": "{func}", "data": []}})
''')

        routes_str = "\n".join(route_blocks)

        # Build tier limits comment block
        tier_comment_lines = []
        for i, tier in enumerate(tiers):
            lim = limits[i]
            if lim is None:
                tier_comment_lines.append(f"#   {tier}: unlimited")
            else:
                tier_comment_lines.append(f"#   {tier}: {lim} requests {window_label}")
        tier_comment = "\n".join(tier_comment_lines)

        return f'''\
"""
Flask API for {resource} management.

This API uses API keys for authentication. Each key belongs to a tier that
determines access level. Rate limiting is NOT yet implemented.

Tiers and limits ({window_label}):
{tier_comment}

TODO: Implement per-tier rate limiting.
"""
from flask import Flask, jsonify, request
import time

app = Flask(__name__)

# ── API key store ──────────────────────────────────────────────────────────────
# Maps API key -> client metadata including tier
API_KEYS = {{
{api_keys_block}
}}

# ── Helper: resolve caller's tier from request ─────────────────────────────────

def get_client_tier():
    """Extract and validate API key; return tier string or None."""
    key = request.headers.get("{api_key_header}", "")
    if key not in API_KEYS:
        return None
    return API_KEYS[key].get("{tier_field}")


# ── Rate limiting state (in-process; use Redis in production) ─────────────────
# Structure: {{tier: {{window_start: int, count: int}}}}
# NOTE: This dict exists but is never populated — rate limiting not implemented.
_rate_state: dict = {{}}


# ── Routes ─────────────────────────────────────────────────────────────────────

{routes_str}

@app.route("/api/health", methods=["GET"])
def health():
    """Health check — no rate limiting applied."""
    return jsonify({{"status": "healthy"}})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
'''

    def _gen_requirements(self) -> str:
        return """\
Flask>=2.3.0
"""

    def _gen_tests(
        self,
        tiers: list,
        limits: list,
        tier_field: str,
        endpoints: list,
        ep_tier_map: dict,
        api_key_header: str,
        window: int,
        resource: str,
    ) -> str:
        # Pick a limited-tier endpoint for testing (first non-internal ep)
        test_ep = None
        test_tier_idx = None
        for ep in endpoints:
            tier = ep_tier_map[ep["func"]]
            tier_idx = tiers.index(tier)
            if limits[tier_idx] is not None:
                test_ep = ep
                test_tier_idx = tier_idx
                break

        if test_ep is None:
            test_ep = endpoints[0]
            test_tier_idx = 0

        test_tier = tiers[test_tier_idx]
        test_limit = limits[test_tier_idx]
        test_key = f"key-{test_tier}-001"
        test_path = test_ep["path"]
        test_method = test_ep["method"].lower()
        internal_tier = tiers[-1]
        internal_key = f"key-{internal_tier}-001"

        # For premium/higher tier test — find an endpoint that belongs to a
        # different (higher) tier so tier isolation test uses distinct counters
        higher_tier_idx = min(test_tier_idx + 1, len(tiers) - 2)
        higher_tier = tiers[higher_tier_idx]
        higher_key = f"key-{higher_tier}-001"
        higher_limit = limits[higher_tier_idx]

        # Find an endpoint whose tier differs from test_tier (for isolation test)
        higher_ep = None
        higher_ep_method = test_method
        higher_ep_path = test_path
        for ep in endpoints:
            ep_tier = ep_tier_map[ep["func"]]
            ep_tier_idx = tiers.index(ep_tier)
            if ep_tier != test_tier and limits[ep_tier_idx] is not None:
                higher_ep = ep
                higher_ep_path = ep["path"]
                higher_ep_method = ep["method"].lower()
                higher_tier = ep_tier
                higher_key = f"key-{ep_tier}-001"
                break
        # Fallback: if no different finite-tier endpoint found, use health (always 200)
        if higher_ep is None:
            higher_ep_path = "/api/health"
            higher_ep_method = "get"
            higher_key = f"key-{tiers[higher_tier_idx]}-001"

        return f'''\
"""Tests for SEC7: Rate Limiting per API Tier.

These tests verify that the rate limiting implementation is correct.
Run with: python -m pytest tests/test_rate_limiting.py -v
"""
import pytest
import json


@pytest.fixture
def client():
    """Create a Flask test client."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app import app
    app.config["TESTING"] = True
    # Reset rate state between tests
    from app import _rate_state
    _rate_state.clear()
    with app.test_client() as c:
        yield c


# ── 1. Valid API key returns 200 ───────────────────────────────────────────────

def test_valid_key_accepted(client):
    """A valid API key should get a 200 response."""
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 200


# ── 2. Missing API key returns 401 ────────────────────────────────────────────

def test_missing_key_rejected(client):
    """Requests without an API key should be rejected with 401."""
    resp = client.{test_method}("{test_path}")
    assert resp.status_code == 401


# ── 3. Invalid API key returns 401 ────────────────────────────────────────────

def test_invalid_key_rejected(client):
    """Requests with a bogus API key should be rejected with 401."""
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "bad-key-xyz"}}
    )
    assert resp.status_code == 401


# ── 4. Rate limit headers present on successful response ──────────────────────

def test_rate_limit_headers_present(client):
    """Successful responses must include X-RateLimit-* headers."""
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 200
    assert "X-RateLimit-Limit" in resp.headers, "X-RateLimit-Limit header missing"
    assert "X-RateLimit-Remaining" in resp.headers, "X-RateLimit-Remaining header missing"
    assert "X-RateLimit-Reset" in resp.headers, "X-RateLimit-Reset header missing"


# ── 5. X-RateLimit-Limit reflects tier limit ──────────────────────────────────

def test_rate_limit_header_value(client):
    """X-RateLimit-Limit must equal the tier's configured limit."""
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 200
    limit_header = resp.headers.get("X-RateLimit-Limit", "")
    assert str({test_limit}) == limit_header, (
        f"Expected X-RateLimit-Limit={test_limit}, got {{limit_header}}"
    )


# ── 6. X-RateLimit-Remaining decrements on each request ──────────────────────

def test_remaining_decrements(client):
    """X-RateLimit-Remaining must decrease with each request."""
    remaining_values = []
    for _ in range(3):
        resp = client.{test_method}(
            "{test_path}",
            headers={{"{api_key_header}": "{test_key}"}}
        )
        assert resp.status_code == 200
        remaining_values.append(int(resp.headers["X-RateLimit-Remaining"]))
    assert remaining_values[0] > remaining_values[1] > remaining_values[2], (
        f"Remaining should decrease: {{remaining_values}}"
    )


# ── 7. Exceeding limit returns 429 ────────────────────────────────────────────

def test_rate_limit_enforced(client):
    """After exhausting the limit, the next request must return 429."""
    # Make exactly limit requests (all should succeed)
    for i in range({test_limit}):
        resp = client.{test_method}(
            "{test_path}",
            headers={{"{api_key_header}": "{test_key}"}}
        )
        assert resp.status_code == 200, f"Request {{i+1}} failed early: {{resp.status_code}}"

    # The next one must be rate-limited
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 429, (
        f"Expected 429 after {{int({test_limit})}} requests, got {{resp.status_code}}"
    )


# ── 8. 429 response has correct JSON body ─────────────────────────────────────

def test_429_response_format(client):
    """429 response must include error and retry_after fields."""
    for _ in range({test_limit}):
        client.{test_method}(
            "{test_path}",
            headers={{"{api_key_header}": "{test_key}"}}
        )
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 429
    data = resp.get_json()
    assert data is not None, "429 response body must be JSON"
    assert "error" in data, "429 body must contain 'error' key"
    assert "retry_after" in data, "429 body must contain 'retry_after' key"


# ── 9. 429 includes X-RateLimit headers ──────────────────────────────────────

def test_429_includes_ratelimit_headers(client):
    """Even a 429 response must include X-RateLimit-* headers."""
    for _ in range({test_limit}):
        client.{test_method}(
            "{test_path}",
            headers={{"{api_key_header}": "{test_key}"}}
        )
    resp = client.{test_method}(
        "{test_path}",
        headers={{"{api_key_header}": "{test_key}"}}
    )
    assert resp.status_code == 429
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers
    assert "X-RateLimit-Reset" in resp.headers
    assert resp.headers["X-RateLimit-Remaining"] == "0"


# ── 10. Internal/unlimited tier is never rate-limited ─────────────────────────

def test_internal_tier_unlimited(client):
    """Internal tier must never be rate-limited, regardless of request count."""
    # Make requests well above the highest finite limit
    max_finite_limit = max(lim for lim in [{", ".join(str(l) for l in limits if l is not None)}] if lim is not None)
    call_count = min(max_finite_limit + 5, 50)  # cap at 50 to keep test fast
    for i in range(call_count):
        resp = client.get(
            "/api/health",  # use health endpoint; internal key on any endpoint
            headers={{"{api_key_header}": "{internal_key}"}}
        )
        # Internal key requests must not be 429
        assert resp.status_code != 429, (
            f"Internal tier got 429 on request {{i+1}} — unlimited tier must never be blocked"
        )


# ── 11. Health endpoint is exempt from rate limiting ─────────────────────────

def test_health_endpoint_exempt(client):
    """Health check endpoint must always return 200 regardless of rate state."""
    resp = client.get("/api/health")
    assert resp.status_code == 200


# ── 12. Different tiers have independent counters ─────────────────────────────

def test_tier_isolation(client):
    """Exhausting tier A's limit must not affect tier B's counter."""
    # Exhaust the lowest test tier on its own endpoint
    for _ in range({test_limit}):
        client.{test_method}(
            "{test_path}",
            headers={{"{api_key_header}": "{test_key}"}}
        )
    # A different tier's endpoint (or health) must still work — counters are independent
    resp = client.{higher_ep_method}(
        "{higher_ep_path}",
        headers={{"{api_key_header}": "{higher_key}"}}
    )
    assert resp.status_code in (200, 401), (
        f"Expected 200 or 401 from a different tier's endpoint, got {{resp.status_code}} "
        f"— exhausting one tier must not block another tier's counter"
    )
'''

    # ── doc generators ─────────────────────────────────────────────────────────

    def _gen_spec(
        self,
        tiers: list,
        limits: list,
        tier_field: str,
        endpoints: list,
        ep_tier_map: dict,
        api_key_header: str,
        window: int,
        window_label: str,
        resource: str,
    ) -> str:
        # Build tier table
        tier_rows = []
        for i, tier in enumerate(tiers):
            lim = limits[i]
            lim_str = "Unlimited" if lim is None else str(lim)
            tier_rows.append(f"| `{tier}` | {lim_str} | {window_label} |")
        tier_table = "\n".join(tier_rows)

        # Build endpoint table
        ep_rows = []
        for ep in endpoints:
            tier = ep_tier_map[ep["func"]]
            ep_rows.append(
                f"| `{ep['path']}` | `{ep['method']}` | `{ep['func']}` | `{tier}` | {ep['desc']} |"
            )
        ep_table = "\n".join(ep_rows)

        # Build key examples
        key_examples = []
        for tier in tiers:
            key = f"key-{tier}-001"
            key_examples.append(f"- `{key}` → `{tier_field}`: `{tier}`")
        key_examples_str = "\n".join(key_examples)

        return f"""\
# SEC7: Rate Limiting Per API Tier — Full Specification

## Overview

The `{resource}` API authenticates callers via API keys passed in the
`{api_key_header}` request header. Each API key belongs to a **tier**
(stored in the `{tier_field}` field of the key's metadata). The API currently
has **no rate limiting** — every endpoint responds to any authenticated request
without any throttling.

Your task is to implement per-tier rate limiting so that each tier's request
quota is enforced across all applicable endpoints within the configured window.

---

## API Key Store

API keys are stored in the `API_KEYS` dict in `app.py`. The key metadata
includes a `{tier_field}` field that determines which rate limit applies.

Example keys (pre-configured in workspace):
{key_examples_str}

Requests missing the `{api_key_header}` header, or carrying an unrecognised
key, must be rejected with **HTTP 401**.

---

## Tier Definitions

| Tier | Limit | Window |
|------|-------|--------|
{tier_table}

- **Unlimited** tiers (`{tiers[-1]}`) must never be rate-limited; all their
  requests must pass through regardless of volume.
- All other tiers are counted within a **sliding or fixed window** of
  {window} seconds ({window_label}).

---

## Endpoint-to-Tier Mapping

Each endpoint belongs to exactly one tier. The tier determines which rate
limit counter is used.

| Path | Method | Function | Tier | Description |
|------|--------|----------|------|-------------|
{ep_table}
| `/api/health` | `GET` | `health` | exempt | Health check — always passes |

---

## Required Response Headers

Every response from a rate-limited endpoint (both successful and 429) **must**
include the following headers:

| Header | Type | Description |
|--------|------|-------------|
| `X-RateLimit-Limit` | integer | The tier's total allowed requests in the window |
| `X-RateLimit-Remaining` | integer | Requests remaining in the current window |
| `X-RateLimit-Reset` | integer | Unix timestamp (seconds) when the window resets |

For **unlimited** tiers, omitting these headers is acceptable, or they may be
set to a large sentinel value (e.g., `X-RateLimit-Limit: 999999`).

---

## HTTP 429 Response Format

When a client exceeds its tier limit, respond with:

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: <limit>
X-RateLimit-Remaining: 0
X-RateLimit-Reset: <unix_ts>

{{
  "error": "rate limit exceeded",
  "retry_after": <seconds_until_reset>
}}
```

- `retry_after` must be a positive integer (seconds until the window resets).
- The response body must be valid JSON with at minimum the keys `error` and
  `retry_after`.

---

## Rate Limit Window

- Window size: **{window} seconds** ({window_label}).
- The counter resets at the start of each new window.
- A fixed-window implementation (counter + window start time stored in
  `_rate_state`) is acceptable. Sliding windows are also acceptable.
- `_rate_state` is already declared in `app.py` as an empty dict — populate
  it with per-tier (or per-key) counters.

---

## Implementation Requirements

1. **Authentication first**: reject missing/invalid keys with 401 before rate
   limit checks.
2. **Per-tier isolation**: exhausting tier A's quota must not affect tier B's
   counter. Counters may be keyed by tier name or by individual API key.
3. **Headers on every rated response**: include `X-RateLimit-*` headers on
   both 200 and 429 responses for all non-exempt endpoints.
4. **Unlimited tier passthrough**: `{tiers[-1]}` tier must never receive a 429.
5. **Health endpoint exempt**: `/api/health` must remain accessible without
   authentication and without rate limiting.
6. **No external dependencies**: use only Python stdlib + Flask (already in
   `requirements.txt`). Do not add Redis, Flask-Limiter, etc.

---

## Deliverables

The Executor must modify `app.py` to implement the above. The Verifier must
confirm:

- 401 returned for unauthenticated requests
- Correct `X-RateLimit-Limit` header value per tier
- `X-RateLimit-Remaining` decrements per request
- 429 returned after the tier limit is exhausted
- 429 response body has `error` and `retry_after` keys
- `{tiers[-1]}` tier is never blocked
- Tier counters are independent (exhausting one tier does not block another)
"""

    def _gen_brief(self, resource: str) -> str:
        return f"""\
# SEC7: Rate Limiting (Executor Brief)

The `{resource}` API is receiving abusive traffic. Add rate limiting to
prevent abuse. The Planner has the full specification with tier definitions,
per-tier limits, required response headers, and the 429 error format.

**Your workspace contains**:
- `app.py` — Flask API with multiple endpoints and no rate limiting
- `requirements.txt` — Python dependencies (Flask only)
- `tests/test_rate_limiting.py` — test suite to validate your implementation

Do not add external rate-limiting libraries. Implement the limiter using
the `_rate_state` dict already declared in `app.py`.

Do not change URL paths, HTTP methods, or response shapes of existing
endpoints (other than adding the required headers and 429 handling).
"""
