"""
Parameterized generator for CR4: API Design Review Fix.

Each seed produces:
- A different API domain (user management, product catalog, order management,
  content/blog, event booking)
- A Flask/Python REST API with 5-8 endpoints containing deliberate design violations:
    Violation 1: Wrong HTTP method (e.g. GET used for create/delete, POST for idempotent fetch)
    Violation 2: Inconsistent naming (camelCase routes, mixed plurals/singulars)
    Violation 3: Missing pagination on list endpoints
    Violation 4: Wrong status codes (e.g. 200 for creation, 200 for not-found, 500 for client errors)
    Violation 5: No API versioning (missing /api/v1/ prefix)
    Violation 6: Missing error schema (bare string errors instead of {"error": "...", "code": "..."})
- A comprehensive API design guidelines document in the spec
- An API review report listing the specific violations (spec-side, TNI Pattern D,C)

TNI driver (Pattern D + C — spec has full review doc + guidelines):
- Brief: "Code review found issues with the API design. Fix them."
- Spec: Complete API review document listing every violation with line references,
  plus the API design guidelines to follow.
- The Executor sees only the brief; Planner coordinates the full fix list.

Seed → domain:
  seed % 5 == 0 → user_management
  seed % 5 == 1 → product_catalog
  seed % 5 == 2 → order_management
  seed % 5 == 3 → content_blog
  seed % 5 == 4 → event_booking
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ---------------------------------------------------------------------------
# Domain definitions
# ---------------------------------------------------------------------------

DOMAINS = [
    {
        "name": "user_management",
        "title": "User Management API",
        "description": "manages user accounts, profiles, and authentication",
        "resource": "user",
        "resources": "users",
        "resource_cap": "User",
        "id_field": "user_id",
        "extra_field_1": "email",
        "extra_field_2": "role",
        "extra_field_3": "is_active",
        "extra_val_1": "admin@example.com",
        "extra_val_2": "admin",
        "extra_val_3": True,
        "sample_filter": "role",
        "sample_filter_val": "admin",
    },
    {
        "name": "product_catalog",
        "title": "Product Catalog API",
        "description": "manages product listings, categories, and inventory",
        "resource": "product",
        "resources": "products",
        "resource_cap": "Product",
        "id_field": "product_id",
        "extra_field_1": "category",
        "extra_field_2": "price",
        "extra_field_3": "in_stock",
        "extra_val_1": "electronics",
        "extra_val_2": 29.99,
        "extra_val_3": True,
        "sample_filter": "category",
        "sample_filter_val": "electronics",
    },
    {
        "name": "order_management",
        "title": "Order Management API",
        "description": "manages customer orders, line items, and fulfillment",
        "resource": "order",
        "resources": "orders",
        "resource_cap": "Order",
        "id_field": "order_id",
        "extra_field_1": "status",
        "extra_field_2": "total",
        "extra_field_3": "customer_id",
        "extra_val_1": "pending",
        "extra_val_2": 149.99,
        "extra_val_3": "cust_001",
        "sample_filter": "status",
        "sample_filter_val": "pending",
    },
    {
        "name": "content_blog",
        "title": "Content/Blog API",
        "description": "manages blog posts, authors, tags, and comments",
        "resource": "post",
        "resources": "posts",
        "resource_cap": "Post",
        "id_field": "post_id",
        "extra_field_1": "title",
        "extra_field_2": "author",
        "extra_field_3": "published",
        "extra_val_1": "Hello World",
        "extra_val_2": "alice",
        "extra_val_3": False,
        "sample_filter": "author",
        "sample_filter_val": "alice",
    },
    {
        "name": "event_booking",
        "title": "Event Booking API",
        "description": "manages events, bookings, venues, and capacity",
        "resource": "event",
        "resources": "events",
        "resource_cap": "Event",
        "id_field": "event_id",
        "extra_field_1": "venue",
        "extra_field_2": "capacity",
        "extra_field_3": "date",
        "extra_val_1": "Grand Hall",
        "extra_val_2": 200,
        "extra_val_3": "2025-06-15",
        "sample_filter": "venue",
        "sample_filter_val": "Grand Hall",
    },
]

# ---------------------------------------------------------------------------
# Violation type pools — each controls one category of bad API design
# ---------------------------------------------------------------------------

# V1: Wrong HTTP method violations (bad_method, correct_method, route_purpose)
WRONG_METHOD_VARIANTS = [
    ("GET",    "POST",   "create"),
    ("GET",    "DELETE", "delete"),
    ("POST",   "GET",    "fetch_by_filter"),
    ("PUT",    "POST",   "create_idempotent"),
    ("DELETE", "POST",   "bulk_delete"),
]

# V2: Inconsistent naming violations (bad_route_style, good_route_style)
NAMING_VARIANTS = [
    ("camelCase",          "snake_case",       "getUser",          "get_user"),
    ("mixed_plural",       "consistent_plural","user/list",        "users"),
    ("camelCase",          "snake_case",       "createProduct",    "create_product"),
    ("mixed_convention",   "snake_case",       "orderItems",       "order_items"),
    ("camelCase",          "snake_case",       "bookEvent",        "book_event"),
]

# V3: Pagination style (missing parameter name, correct parameter name)
PAGINATION_VARIANTS = [
    ("no pagination — returns all records without limit/offset",
     "page + page_size query parameters", "page", "page_size"),
    ("no pagination — unbounded list response",
     "cursor-based: cursor + limit query parameters", "cursor", "limit"),
    ("no pagination — full dataset returned on every call",
     "page + per_page query parameters", "page", "per_page"),
    ("no pagination — count not returned in response",
     "page + page_size with total_count in response", "page", "page_size"),
    ("no pagination — missing offset support",
     "offset + limit query parameters", "offset", "limit"),
]

# V4: Wrong status codes (bad_code, good_code, context)
STATUS_CODE_VARIANTS = [
    (200, 201, "resource creation should return 201 Created"),
    (200, 404, "not-found should return 404 Not Found"),
    (500, 400, "client validation errors should return 400 Bad Request"),
    (200, 204, "successful deletion should return 204 No Content"),
    (200, 422, "validation failures should return 422 Unprocessable Entity"),
]

# V5: Versioning (bad_prefix, good_prefix)
VERSIONING_VARIANTS = [
    ("no prefix",      "/api/v1/"),
    ("/api/",          "/api/v1/"),
    ("/v1/",           "/api/v1/"),
    ("no prefix",      "/api/v1/"),
    ("/api/",          "/api/v1/"),
]

# V6: Error schema (bad_schema, good_schema)
ERROR_SCHEMA_VARIANTS = [
    ('return "Not found", 404',
     'return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404'),
    ('return "Bad request", 400',
     'return jsonify({"error": "Invalid input", "code": "INVALID_INPUT"}), 400'),
    ('return "Error: " + str(e), 500',
     'return jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR"}), 500'),
    ('return "Unauthorized", 401',
     'return jsonify({"error": "Authentication required", "code": "UNAUTHORIZED"}), 401'),
    ('return "Conflict", 409',
     'return jsonify({"error": "Resource already exists", "code": "CONFLICT"}), 409'),
]


class Generator(TaskGenerator):
    task_id = "CR4_api_review"
    domain = "code_review"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        domain = DOMAINS[seed % len(DOMAINS)]

        v1_bad_method, v1_good_method, v1_purpose = WRONG_METHOD_VARIANTS[
            rng.randint(0, len(WRONG_METHOD_VARIANTS) - 1)
        ]
        v2_bad_style, v2_good_style, v2_bad_name, v2_good_name = NAMING_VARIANTS[
            rng.randint(0, len(NAMING_VARIANTS) - 1)
        ]
        v3_bad_desc, v3_good_desc, v3_param1, v3_param2 = PAGINATION_VARIANTS[
            rng.randint(0, len(PAGINATION_VARIANTS) - 1)
        ]
        v4_bad_code, v4_good_code, v4_context = STATUS_CODE_VARIANTS[
            rng.randint(0, len(STATUS_CODE_VARIANTS) - 1)
        ]
        v5_bad_prefix, v5_good_prefix = VERSIONING_VARIANTS[seed % len(VERSIONING_VARIANTS)]
        v6_bad_schema, v6_good_schema = ERROR_SCHEMA_VARIANTS[
            rng.randint(0, len(ERROR_SCHEMA_VARIANTS) - 1)
        ]

        # Port number varies by seed for realism
        port = 5000 + (seed % 10) * 100

        workspace_files = {
            "app.py": self._generate_app(
                domain, v1_bad_method, v1_purpose,
                v2_bad_name, v2_good_name,
                v3_param1, v3_param2,
                v4_bad_code, v4_good_code,
                v5_bad_prefix, v5_good_prefix,
                v6_bad_schema,
                port,
            ),
            "requirements.txt": "flask>=2.3.0\npytest>=7.0.0\npytest-flask>=1.2.0\n",
            "tests/__init__.py": "",
            "tests/test_api.py": self._generate_tests(
                domain, v5_good_prefix, v4_good_code, v3_param1, v3_param2
            ),
        }

        expected = {
            "domain": domain["name"],
            "resource": domain["resource"],
            "resources": domain["resources"],
            "v1_bad_method": v1_bad_method,
            "v1_good_method": v1_good_method,
            "v1_purpose": v1_purpose,
            "v2_bad_name": v2_bad_name,
            "v2_good_name": v2_good_name,
            "v3_param1": v3_param1,
            "v3_param2": v3_param2,
            "v4_bad_code": v4_bad_code,
            "v4_good_code": v4_good_code,
            "v5_good_prefix": v5_good_prefix,
            "v6_bad_schema_fragment": "\"error\":",
            "port": port,
        }

        spec_md = self._generate_spec(
            domain,
            v1_bad_method, v1_good_method, v1_purpose,
            v2_bad_style, v2_good_style, v2_bad_name, v2_good_name,
            v3_bad_desc, v3_good_desc, v3_param1, v3_param2,
            v4_bad_code, v4_good_code, v4_context,
            v5_bad_prefix, v5_good_prefix,
            v6_bad_schema, v6_good_schema,
        )
        brief_md = self._generate_brief(domain)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ------------------------------------------------------------------
    # Workspace: Flask app with deliberate violations
    # ------------------------------------------------------------------

    def _generate_app(
        self,
        domain: dict,
        v1_bad_method: str,
        v1_purpose: str,
        v2_bad_name: str,
        v2_good_name: str,
        v3_param1: str,
        v3_param2: str,
        v4_bad_code: int,
        v4_good_code: int,
        v5_bad_prefix: str,
        v5_good_prefix: str,
        v6_bad_schema: str,
        port: int,
    ) -> str:
        r = domain["resource"]
        rs = domain["resources"]
        rc = domain["resource_cap"]
        id_f = domain["id_field"]
        ef1 = domain["extra_field_1"]
        ef2 = domain["extra_field_2"]
        ef3 = domain["extra_field_3"]
        ev1 = repr(domain["extra_val_1"])
        ev2 = repr(domain["extra_val_2"])
        ev3 = repr(domain["extra_val_3"])
        sf = domain["sample_filter"]
        sfv = repr(domain["sample_filter_val"])

        # Determine route prefix for violations
        # V5: wrong prefix (either none or short /api/)
        if v5_bad_prefix == "no prefix":
            route_prefix = f"/{rs}"
            search_prefix = f"/{rs}"
        elif v5_bad_prefix == "/v1/":
            route_prefix = f"/v1/{rs}"
            search_prefix = f"/v1/{rs}"
        else:
            route_prefix = f"/api/{rs}"
            search_prefix = f"/api/{rs}"

        # V1: violating HTTP method on create endpoint
        create_method = v1_bad_method if v1_purpose == "create" else "POST"

        # V4: violating status code on create
        create_status = v4_bad_code if v4_good_code == 201 else 201
        notfound_status = v4_bad_code if v4_good_code == 404 else 404
        delete_status = v4_bad_code if v4_good_code == 204 else 204

        # V2: camelCase endpoint for search/filter
        search_route = f"/{v2_bad_name}"

        # V6: raw string error (no JSON error schema)
        error_str = v6_bad_schema

        return f'''"""
{domain["title"]}

This module implements a REST API for {domain["description"]}.

NOTE: This file contains several API design issues identified in code review.
See the review report for the list of violations to fix.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory store
_{rs}_store: dict = {{}}
_next_id: int = 1


def _next_{r}_id() -> str:
    global _next_id
    _next_id += 1
    return f"{r}_{{_next_id - 1}}"


# ---------------------------------------------------------------------------
# VIOLATION V5: Routes use "{v5_bad_prefix}" prefix instead of /api/v1/
# VIOLATION V1: Wrong HTTP method on create endpoint
# VIOLATION V2: Inconsistent naming (camelCase route for search)
# VIOLATION V3: List endpoint missing pagination
# VIOLATION V4: Wrong status codes
# VIOLATION V6: Raw string errors (no JSON error schema)
# ---------------------------------------------------------------------------


@app.route("{route_prefix}", methods=["GET"])
def list_{rs}():
    """List all {rs}.

    VIOLATION V3: No pagination — returns all records unconditionally.
    """
    # BUG V3: No page/offset/limit parameters — returns entire dataset
    items = list(_{rs}_store.values())
    return jsonify({{"{rs}": items, "count": len(items)}})


@app.route("{route_prefix}", methods=["{create_method}"])
def create_{r}():
    """Create a new {r}.

    VIOLATION V1: Uses {create_method} instead of POST.
    VIOLATION V4: Returns {create_status} instead of 201 on success.
    """
    data = request.get_json(force=True) or {{}}
    if not data.get("{ef1}"):
        # BUG V6: raw string error, not JSON error schema
        return {error_str}
    rid = _next_{r}_id()
    record = {{
        "{id_f}": rid,
        "{ef1}": data["{ef1}"],
        "{ef2}": data.get("{ef2}"),
        "{ef3}": data.get("{ef3}", False),
    }}
    _{rs}_store[rid] = record
    # BUG V4: should be {v4_good_code if v4_good_code == 201 else 201}, not {create_status}
    return jsonify(record), {create_status}


@app.route("{route_prefix}/<{r}_id>", methods=["GET"])
def get_{r}({r}_id: str):
    """Get a single {r} by ID.

    VIOLATION V4: Returns {notfound_status} as plain text for missing resource.
    VIOLATION V6: Error is a raw string, not a JSON schema.
    """
    record = _{rs}_store.get({r}_id)
    if record is None:
        # BUG V4+V6: should be JSON 404, not a bare string
        return {error_str}, {notfound_status}
    return jsonify(record)


@app.route("{route_prefix}/<{r}_id>", methods=["PUT"])
def update_{r}({r}_id: str):
    """Update an existing {r}."""
    record = _{rs}_store.get({r}_id)
    if record is None:
        # BUG V6: raw string error
        return {error_str}, 404
    data = request.get_json(force=True) or {{}}
    record.update({{k: v for k, v in data.items() if k != "{id_f}"}})
    _{rs}_store[{r}_id] = record
    return jsonify(record)


@app.route("{route_prefix}/<{r}_id>", methods=["DELETE"])
def delete_{r}({r}_id: str):
    """Delete a {r}.

    VIOLATION V4: Returns {delete_status} instead of 204 No Content.
    """
    record = _{rs}_store.pop({r}_id, None)
    if record is None:
        # BUG V6: raw string error
        return {error_str}, 404
    # BUG V4: should return 204, not {delete_status}
    return jsonify({{"deleted": True}}), {delete_status}


# VIOLATION V2: Route uses camelCase "{v2_bad_name}" instead of snake_case "{v2_good_name}"
@app.route("{search_prefix}/{v2_bad_name}", methods=["GET"])
def {v2_bad_name}():
    """Search/filter {rs}.

    VIOLATION V2: Route and function use camelCase naming.
    """
    filter_val = request.args.get("{sf}")
    results = [
        item for item in _{rs}_store.values()
        if filter_val is None or str(item.get("{sf}")) == str(filter_val)
    ]
    return jsonify({{"{rs}": results}})


@app.route("{route_prefix}/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({{"status": "ok", "service": "{domain["title"]}"}})


@app.route("{route_prefix}/stats", methods=["GET"])
def get_stats():
    """Return aggregate statistics.

    VIOLATION V4: Returns 500 for any unexpected error instead of 400 for client errors.
    """
    try:
        group_by = request.args.get("group_by", "{ef1}")
        if group_by not in ("{ef1}", "{ef2}", "{ef3}"):
            # BUG V4+V6: should be 400 with JSON error, not 500
            return {error_str}, 500
        counts: dict = {{}}
        for item in _{rs}_store.values():
            key = str(item.get(group_by, "unknown"))
            counts[key] = counts.get(key, 0) + 1
        return jsonify({{"group_by": group_by, "counts": counts, "total": len(_{rs}_store)}})
    except Exception as exc:
        return {error_str}, 500


if __name__ == "__main__":
    app.run(debug=True, port={port})
'''

    # ------------------------------------------------------------------
    # Tests — validate the FIXED version (correct routes, methods, codes)
    # ------------------------------------------------------------------

    def _generate_tests(
        self,
        domain: dict,
        good_prefix: str,
        v4_good_code: int,
        v3_param1: str,
        v3_param2: str,
    ) -> str:
        r = domain["resource"]
        rs = domain["resources"]
        ef1 = domain["extra_field_1"]
        ef2 = domain["extra_field_2"]
        ev1 = repr(domain["extra_val_1"])
        ev2 = repr(domain["extra_val_2"])
        sf = domain["sample_filter"]
        sfv = repr(domain["sample_filter_val"])

        # After fix, routes should use /api/v1/<resources>
        base = f"{good_prefix}{rs}"
        # Search endpoint uses snake_case after fix
        search_route = f"{good_prefix}{rs}/search"

        return f'''"""
Integration tests for the FIXED {domain["title"]}.

These tests verify the API after all design violations have been corrected:
- /api/v1/ prefix on all routes
- POST for create, DELETE returning 204
- Pagination parameters accepted on list endpoint
- JSON error schema on all errors
- snake_case route naming
"""
import json
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── V5: Versioned routes ─────────────────────────────────────────────────────

def test_list_{rs}_route_exists(client):
    """GET {base} must exist (verifies /api/v1/ prefix)."""
    resp = client.get("{base}")
    assert resp.status_code == 200


def test_health_check_versioned(client):
    """Health check must be under versioned prefix."""
    resp = client.get("{base}/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


# ── V1: Correct HTTP methods ─────────────────────────────────────────────────

def test_create_{r}_uses_post(client):
    """Create must use POST."""
    payload = {{"{ef1}": {ev1}, "{ef2}": {ev2}}}
    resp = client.post("{base}", json=payload)
    # Should NOT be 405 Method Not Allowed
    assert resp.status_code != 405, "POST not allowed — HTTP method violation not fixed"


def test_get_{r}_uses_get(client):
    """Read must use GET."""
    resp = client.get("{base}/nonexistent_id")
    assert resp.status_code in (404, 200)  # 404 expected; not 405


# ── V4: Correct status codes ─────────────────────────────────────────────────

def test_create_{r}_returns_201(client):
    """Create must return 201 Created."""
    payload = {{"{ef1}": {ev1}, "{ef2}": {ev2}}}
    resp = client.post("{base}", json=payload)
    assert resp.status_code == 201, f"Expected 201, got {{resp.status_code}}"


def test_get_{r}_not_found_returns_404(client):
    """Missing resource must return 404."""
    resp = client.get("{base}/does_not_exist_99")
    assert resp.status_code == 404, f"Expected 404, got {{resp.status_code}}"


def test_delete_{r}_returns_204(client):
    """Delete must return 204 No Content."""
    # First create
    payload = {{"{ef1}": {ev1}, "{ef2}": {ev2}}}
    create_resp = client.post("{base}", json=payload)
    assert create_resp.status_code == 201
    rid = create_resp.get_json()[list(create_resp.get_json().keys())[0]]
    # Delete it — find the id field
    created = create_resp.get_json()
    id_val = next(v for k, v in created.items() if "id" in k.lower())
    del_resp = client.delete(f"{base}/{{id_val}}")
    assert del_resp.status_code == 204, f"Expected 204, got {{del_resp.status_code}}"


# ── V6: JSON error schema ────────────────────────────────────────────────────

def test_not_found_returns_json_error(client):
    """404 response must be JSON with error and code fields."""
    resp = client.get("{base}/no_such_id_xyz")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data is not None, "404 response must be JSON, not a plain string"
    assert "error" in data, f"JSON error body must have 'error' key, got: {{data}}"
    assert "code" in data, f"JSON error body must have 'code' key, got: {{data}}"


def test_bad_request_returns_json_error(client):
    """400 response must be JSON with error and code fields."""
    # Send empty body — should trigger validation error
    resp = client.post("{base}", json={{}})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data is not None, "400 response must be JSON"
    assert "error" in data
    assert "code" in data


# ── V3: Pagination ───────────────────────────────────────────────────────────

def test_list_{rs}_accepts_pagination(client):
    """List endpoint must accept {v3_param1} and {v3_param2} query params."""
    resp = client.get("{base}?{v3_param1}=1&{v3_param2}=10")
    assert resp.status_code == 200, (
        f"List with pagination params returned {{resp.status_code}} — "
        "pagination query parameters not supported"
    )
    data = resp.get_json()
    assert "{rs}" in data or "items" in data, "Response must contain resource list"


def test_list_{rs}_respects_page_size(client):
    """List endpoint must limit results when {v3_param2} is provided."""
    # Seed some data
    for i in range(5):
        client.post("{base}", json={{"{ef1}": f"item_{{i}}", "{ef2}": {ev2}}})
    resp = client.get("{base}?{v3_param1}=1&{v3_param2}=2")
    assert resp.status_code == 200
    data = resp.get_json()
    items_key = "{rs}" if "{rs}" in data else "items"
    if items_key in data:
        assert len(data[items_key]) <= 2, (
            f"Page size={v3_param2} not respected — got {{len(data[items_key])}} items"
        )


# ── V2: snake_case routes ────────────────────────────────────────────────────

def test_search_route_uses_snake_case(client):
    """Search route must use snake_case, not camelCase."""
    resp = client.get("{base}/search?{sf}={{sfv}}")
    # camelCase route should return 404 (old route gone), snake_case should work
    assert resp.status_code != 404 or resp.status_code == 200, (
        "snake_case search route not found — naming violation not fixed"
    )
'''

    # ------------------------------------------------------------------
    # Spec: Full API review document + guidelines (Planner-only context)
    # ------------------------------------------------------------------

    def _generate_spec(
        self,
        domain: dict,
        v1_bad_method: str, v1_good_method: str, v1_purpose: str,
        v2_bad_style: str, v2_good_style: str, v2_bad_name: str, v2_good_name: str,
        v3_bad_desc: str, v3_good_desc: str, v3_param1: str, v3_param2: str,
        v4_bad_code: int, v4_good_code: int, v4_context: str,
        v5_bad_prefix: str, v5_good_prefix: str,
        v6_bad_schema: str, v6_good_schema: str,
    ) -> str:
        r = domain["resource"]
        rs = domain["resources"]
        rc = domain["resource_cap"]
        ef1 = domain["extra_field_1"]
        ef2 = domain["extra_field_2"]

        return f"""# CR4: API Design Review Fix

## Goal
Fix all API design violations identified in the code review of `app.py`.
The file must comply with the API Design Guidelines below after your changes.

All existing tests in `tests/test_api.py` must pass.

---

## Module Under Review

**{domain["title"]}** — `app.py`

This module {domain["description"]}.

---

## API Design Guidelines

These guidelines apply to all REST APIs in this organisation.

### G1 — HTTP Methods
- **GET** for read-only retrieval (never modifies state)
- **POST** for creating new resources
- **PUT** / **PATCH** for updating existing resources
- **DELETE** for removing resources
- Never use GET to trigger mutations.

### G2 — Naming Conventions
- All route paths must use **snake_case** (e.g., `/search_results`, not `/searchResults`)
- Route segments must be consistent: always plural nouns for collections (e.g., `/{rs}`)
- Function names must mirror their route using snake_case

### G3 — Pagination
- Every collection endpoint (`GET /{rs}`) **must** support pagination
- Required query parameters: `{v3_param1}` and `{v3_param2}`
- Response must include the paginated slice only — never return the entire dataset
- Response envelope: `{{"{rs}": [...], "{v3_param1}": <n>, "{v3_param2}": <n>, "total": <count>}}`

### G4 — Status Codes
| Operation | Success Code | Notes |
|-----------|-------------|-------|
| Create (POST) | **201 Created** | Body contains new resource |
| Read (GET) | 200 OK | |
| Update (PUT/PATCH) | 200 OK | Body contains updated resource |
| Delete (DELETE) | **204 No Content** | Empty body |
| Not found | **404 Not Found** | JSON error body required |
| Client error | **400 Bad Request** | JSON error body required |
| Validation failure | **422 Unprocessable Entity** | JSON error body |
| Server error | 500 Internal Server Error | JSON error body |

### G5 — API Versioning
- All API routes **must** be prefixed with `/api/v1/`
- Example: `GET /api/v1/{rs}` (not `GET /{rs}` or `GET /api/{rs}`)

### G6 — Error Schema
Every non-2xx response **must** return a JSON body conforming to:
```json
{{
  "error": "<human-readable message>",
  "code":  "<SCREAMING_SNAKE_CASE error code>"
}}
```
Bare string responses (`return "Not found", 404`) are not permitted.

---

## Code Review Findings for `app.py`

The following violations were found during code review. **All must be fixed.**

---

### VIOLATION V1 — Wrong HTTP Method (G1)

**Location**: `create_{r}()` route decorator

**Problem**: The create endpoint is decorated with `methods=["{v1_bad_method}"]`.
Creating a resource requires a state-mutating method.

**Fix**: Change the decorator to `methods=["POST"]`.

Before:
```python
@app.route("...", methods=["{v1_bad_method}"])
def create_{r}():
```

After:
```python
@app.route("...", methods=["POST"])
def create_{r}():
```

---

### VIOLATION V2 — Inconsistent Route Naming (G2)

**Location**: Search/filter endpoint route and function name

**Problem**: The route uses `{v2_bad_style}` naming (`{v2_bad_name}`).
All routes must use `{v2_good_style}` (`{v2_good_name}`).

**Fix**: Rename the route path segment and the function.

Before:
```python
@app.route(".../{v2_bad_name}", methods=["GET"])
def {v2_bad_name}():
```

After:
```python
@app.route(".../search", methods=["GET"])
def search_{rs}():
```

---

### VIOLATION V3 — Missing Pagination on List Endpoint (G3)

**Location**: `list_{rs}()` — `GET /{rs}`

**Problem**: {v3_bad_desc}.
Returning unbounded datasets causes performance and reliability issues.

**Fix**: Add `{v3_param1}` and `{v3_param2}` query parameters; slice the result.

After:
```python
@app.route("/api/v1/{rs}", methods=["GET"])
def list_{rs}():
    {v3_param1} = int(request.args.get("{v3_param1}", 1))
    {v3_param2} = int(request.args.get("{v3_param2}", 20))
    items = list(_{rs}_store.values())
    start = ({v3_param1} - 1) * {v3_param2}
    end   = start + {v3_param2}
    return jsonify({{
        "{rs}": items[start:end],
        "{v3_param1}": {v3_param1},
        "{v3_param2}": {v3_param2},
        "total": len(items),
    }})
```

---

### VIOLATION V4 — Wrong HTTP Status Codes (G4)

**Locations**:
1. `create_{r}()` — returns `{v4_bad_code}` instead of `201` on success
2. `get_{r}()` — returns `{v4_bad_code}` instead of `404` for missing resource
3. `delete_{r}()` — returns `{v4_bad_code}` instead of `204` on success
4. `get_stats()` — returns `500` instead of `400` for client-supplied bad `group_by` value

**Fix**: Update every `return ..., STATUS` to use the correct code per G4.

---

### VIOLATION V5 — Missing API Versioning (G5)

**Problem**: All routes use `{v5_bad_prefix}` prefix instead of `/api/v1/`.

**Fix**: Replace all route prefixes with `/api/v1/`.

Before:
```python
@app.route("/{rs}", ...)
@app.route("/{rs}/<{r}_id>", ...)
```

After:
```python
@app.route("/api/v1/{rs}", ...)
@app.route("/api/v1/{rs}/<{r}_id>", ...)
```

---

### VIOLATION V6 — Missing JSON Error Schema (G6)

**Locations**: Every non-2xx return in `app.py` uses a bare string:

```python
{v6_bad_schema}
```

**Fix**: Replace every error return with a `jsonify()` call conforming to G6:

```python
{v6_good_schema}
```

Apply this pattern to **all** error responses: 404 (not found), 400 (bad input),
500 (server errors), and any other non-2xx status.

---

## Summary of All Required Changes

| # | Violation | Location(s) | Fix |
|---|-----------|-------------|-----|
| V1 | Wrong HTTP method (`{v1_bad_method}` → POST) | `create_{r}()` | Change decorator method |
| V2 | camelCase route (`{v2_bad_name}` → `search_{rs}`) | search route + function | Rename route & function |
| V3 | No pagination | `list_{rs}()` | Add `{v3_param1}` + `{v3_param2}` params |
| V4 | Wrong status codes ({v4_bad_code} → 201/404/204/400) | create, get, delete, stats | Fix return codes |
| V5 | Missing `/api/v1/` prefix | all routes | Add versioned prefix |
| V6 | Bare string errors | all error returns | Wrap with `jsonify({{"error":..., "code":...}})` |

## Deliverables
1. `app.py` with all six violations corrected.
2. `tests/test_api.py` must pass without modification.
3. Verifier writes `attestation.json` with `verdict: pass` once all checks pass.
"""

    # ------------------------------------------------------------------
    # Brief: Minimal context for Executor (TNI Pattern D,C)
    # ------------------------------------------------------------------

    def _generate_brief(self, domain: dict) -> str:
        r = domain["resource"]
        rs = domain["resources"]

        return f"""# CR4: API Design Fix (Brief)

## Your Task
The **{domain["title"]}** (`app.py`) was flagged during code review for multiple
API design violations.

Fix all the violations so the API conforms to the team's REST API design guidelines.

## What You Know
- The API is in `app.py` (Flask/Python).
- The code review found issues with: HTTP methods, route naming, pagination,
  status codes, API versioning, and error responses.
- `tests/test_api.py` must pass without any modification after your fixes.
- Do NOT modify `tests/test_api.py`.
- Install dependencies with `pip install -r requirements.txt` before running tests.

## What the Planner Has
The Planner has the full API review report listing every violation with exact
locations and the required fixes. Follow the Planner's instructions precisely.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/test_api.py -v
```
"""
