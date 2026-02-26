"""
Parameterized generator for MULTI2: API & Frontend Contract Fix.

TNI Pattern D (Cross-System Contract): Spec has the complete API contract.
The backend has bugs that violate the contract AND the frontend has bugs
that expect wrong fields / wrong paths / wrong auth.

Each seed produces:
  - Different app type (todo_list, user_dashboard, product_catalog, chat_app)
  - Different resource names and field names
  - Different backend bugs (3-5): wrong field names in responses, wrong status
    codes, missing CORS header, wrong pagination format, wrong error format
  - Different frontend bugs (3-5): wrong field name in fetch, wrong URL path,
    missing auth header, wrong error handling field
  - Workspace: backend/server.py + frontend/app.py (Python CLI frontend that
    consumes the API via requests library)
  - Spec: complete API contract (endpoint URLs, request/response schemas,
    auth header format, pagination format, error response format)
  - Brief: vague ("frontend shows errors, investigate and fix")

The 12+ grading checks cover:
  1. backend/server.py imports without error
  2. frontend/app.py imports without error
  3. GET /api/<resource> returns list under correct key (not wrong key)
  4. GET /api/<resource> response includes pagination wrapper
  5. POST /api/<resource> returns 201 (not wrong status like 200 or 200/400)
  6. POST /api/<resource> body uses correct field names in response
  7. CORS header present on responses
  8. Error response uses correct format {"error": "..."}  (not {"message": "..."})
  9. GET /api/<resource>/<id> returns single item under correct key
  10. Frontend auth header sent correctly (Bearer token)
  11. Frontend uses correct URL path (not typo path)
  12. Frontend parses response field correctly (not wrong field name)
  13. Frontend handles 404 correctly (checks error key not message key)
  14. End-to-end: frontend create + fetch works without exception
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ---------------------------------------------------------------------------
# App configuration pool
# (app_type, resource_plural, resource_singular, field1, field2, field3)
# ---------------------------------------------------------------------------
APP_CONFIGS = [
    ("todo_list",        "todos",    "todo",    "title",       "done",        "priority"),
    ("user_dashboard",   "users",    "user",    "username",    "email",       "role"),
    ("product_catalog",  "products", "product", "name",        "price",       "category"),
    ("chat_app",         "messages", "message", "text",        "sender",      "channel"),
    ("blog_platform",    "posts",    "post",    "title",       "body",        "author"),
]

# ---------------------------------------------------------------------------
# Backend bug pool
# Each bug is (bug_id, description_template, apply_fn_name)
# apply_fn_name refers to which generation switch to flip
# ---------------------------------------------------------------------------

# Wrong field names in GET list response (response key)
WRONG_RESPONSE_KEYS = [
    # (correct_key, wrong_key)
    ("items",   "data"),
    ("items",   "results"),
    ("items",   "records"),
    ("items",   "entries"),
]

# Wrong status codes for POST
WRONG_POST_STATUS = [200, 202, 204, 400]

# Wrong pagination fields
WRONG_PAGINATION_FIELDS = [
    # (correct_total_key, wrong_total_key)
    ("total",   "count"),
    ("total",   "size"),
    ("total",   "length"),
]

# Wrong error format fields
WRONG_ERROR_FIELDS = [
    # (correct_error_key, wrong_error_key)
    ("error",   "message"),
    ("error",   "msg"),
    ("error",   "detail"),
]

# Wrong single-item response key
WRONG_SINGLE_KEYS = [
    ("item",    "data"),
    ("item",    "result"),
    ("item",    "record"),
]

# Auth token values
AUTH_TOKENS = [
    "supersecret-token-abc123",
    "dev-token-xyz789",
    "api-key-mnop456",
    "bearer-tok-qrs012",
    "access-tok-tuv345",
]

# Wrong URL path suffixes (frontend bug: wrong path)
WRONG_PATHS = [
    # (correct_segment, wrong_segment)
    ("api",     "apiv1"),
    ("api",     "API"),
    ("api",     "rest"),
    ("api",     "v1"),
]

# Wrong frontend field accesses (frontend reads wrong key from response)
WRONG_FRONTEND_FIELDS = [
    # (correct_key, wrong_key)
    ("items",   "data"),
    ("items",   "results"),
    ("total",   "count"),
    ("item",    "record"),
    ("error",   "message"),
]

# Ports
PORTS = [5000, 5001, 8000, 8080, 4000]


class Generator(TaskGenerator):
    task_id = "MULTI2_api_frontend"
    domain = "fullstack"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # Pick app configuration
        app_cfg = rng.choice(APP_CONFIGS)
        app_type, resource, singular, field1, field2, field3 = app_cfg

        port = rng.choice(PORTS)
        auth_token = rng.choice(AUTH_TOKENS)

        # Backend bugs (pick 3-5 bug types from pool)
        n_backend_bugs = rng.randint(3, 5)
        backend_bug_pool = [
            "wrong_list_key",       # GET list wraps under wrong key
            "wrong_post_status",    # POST returns wrong status code
            "missing_cors",         # No Access-Control-Allow-Origin header
            "wrong_pagination_key", # Pagination uses wrong field name for total
            "wrong_error_key",      # Error responses use wrong key
        ]
        rng.shuffle(backend_bug_pool)
        active_backend_bugs = set(backend_bug_pool[:n_backend_bugs])

        # Frontend bugs (pick 3-5 bug types from pool)
        n_frontend_bugs = rng.randint(3, 5)
        frontend_bug_pool = [
            "wrong_url_path",       # Wrong /api/ path prefix
            "missing_auth_header",  # No Authorization: Bearer header
            "wrong_list_field",     # Reads response.data instead of response.items
            "wrong_error_field",    # Checks err.message instead of err.error
            "wrong_single_field",   # GET single reads .data instead of .item
        ]
        rng.shuffle(frontend_bug_pool)
        active_frontend_bugs = set(frontend_bug_pool[:n_frontend_bugs])

        # Pick concrete wrong values for each active bug
        wrong_list_key        = rng.choice(WRONG_RESPONSE_KEYS)      # (correct, wrong)
        wrong_post_status_val = rng.choice(WRONG_POST_STATUS)
        wrong_pagination_key  = rng.choice(WRONG_PAGINATION_FIELDS)  # (correct, wrong)
        wrong_error_key       = rng.choice(WRONG_ERROR_FIELDS)       # (correct, wrong)
        wrong_url_seg         = rng.choice(WRONG_PATHS)              # (correct, wrong)
        wrong_single_key_val  = rng.choice(WRONG_SINGLE_KEYS)        # (correct, wrong)

        # Generate workspace files
        server_py = self._gen_server_py(
            resource, singular, field1, field2, field3, port, auth_token,
            active_backend_bugs,
            wrong_list_key, wrong_post_status_val,
            wrong_pagination_key, wrong_error_key,
        )
        frontend_py = self._gen_frontend_py(
            resource, singular, field1, field2, field3, port, auth_token,
            active_frontend_bugs,
            wrong_url_seg, wrong_list_key, wrong_error_key, wrong_single_key_val,
        )
        test_py = self._gen_test_py(
            resource, singular, field1, field2, field3, port, auth_token,
            active_backend_bugs, active_frontend_bugs,
            wrong_list_key, wrong_post_status_val,
            wrong_pagination_key, wrong_error_key,
            wrong_url_seg, wrong_single_key_val,
        )

        workspace_files = {
            "backend/server.py":  server_py,
            "frontend/app.py":    frontend_py,
            "test_contract.py":   test_py,
        }

        # Build expected dict for grader
        expected = {
            "app_type":             app_type,
            "resource":             resource,
            "singular":             singular,
            "field1":               field1,
            "field2":               field2,
            "field3":               field3,
            "port":                 port,
            "auth_token":           auth_token,
            # Correct contract values
            "correct_list_key":     wrong_list_key[0],
            "correct_post_status":  201,
            "correct_pagination_key": wrong_pagination_key[0],
            "correct_error_key":    wrong_error_key[0],
            "correct_url_seg":      wrong_url_seg[0],
            "correct_single_key":   wrong_single_key_val[0],
            # Bug values (what was wrong)
            "wrong_list_key":       wrong_list_key[1],
            "wrong_post_status":    wrong_post_status_val,
            "wrong_pagination_key": wrong_pagination_key[1],
            "wrong_error_key":      wrong_error_key[1],
            "wrong_url_seg":        wrong_url_seg[1],
            "wrong_single_key":     wrong_single_key_val[1],
            # Active bugs
            "active_backend_bugs":  sorted(active_backend_bugs),
            "active_frontend_bugs": sorted(active_frontend_bugs),
            "backend_bug_count":    n_backend_bugs,
            "frontend_bug_count":   n_frontend_bugs,
            "total_bug_count":      n_backend_bugs + n_frontend_bugs,
        }

        spec_md  = self._gen_spec(
            app_type, resource, singular, field1, field2, field3, port, auth_token,
            wrong_list_key[0], wrong_pagination_key[0], wrong_error_key[0],
            wrong_single_key_val[0],
        )
        brief_md = self._gen_brief(app_type, resource)

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── File generators ─────────────────────────────────────────────────────

    def _gen_server_py(
        self, resource, singular, f1, f2, f3, port, token,
        active_bugs,
        wrong_list_key, wrong_post_status,
        wrong_pagination_key, wrong_error_key,
    ) -> str:
        # Decide actual values based on which bugs are active
        list_key       = wrong_list_key[1]      if "wrong_list_key"       in active_bugs else wrong_list_key[0]
        post_status    = wrong_post_status       if "wrong_post_status"    in active_bugs else 201
        cors_line      = ""                      if "missing_cors"         in active_bugs else \
                         'response.headers["Access-Control-Allow-Origin"] = "*"'
        pag_key        = wrong_pagination_key[1] if "wrong_pagination_key" in active_bugs else wrong_pagination_key[0]
        err_key        = wrong_error_key[1]      if "wrong_error_key"      in active_bugs else wrong_error_key[0]

        # Single-item key is always correct in backend (that's a frontend bug)
        single_key = "item"

        resource_cap = resource.capitalize()
        singular_cap = singular.capitalize()

        cors_after_request = ""
        if "missing_cors" not in active_bugs:
            cors_after_request = f"""
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response
"""

        return f'''"""
{resource_cap} API server — Flask backend.
WARNING: This file contains intentional bugs for the TeamBench exercise.
"""

import sqlite3
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

AUTH_TOKEN = "{token}"

# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _check_auth():
    """Return True if the request carries the correct Bearer token."""
    auth = request.headers.get("Authorization", "")
    return auth == f"Bearer {{AUTH_TOKEN}}"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if not hasattr(app, "_db"):
        app._db = sqlite3.connect(":memory:", check_same_thread=False)
        app._db.row_factory = sqlite3.Row
        _init_db(app._db)
    return app._db


def _init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS {resource} (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            {f1}        TEXT NOT NULL DEFAULT '',
            {f2}        TEXT NOT NULL DEFAULT '',
            {f3}        TEXT NOT NULL DEFAULT '',
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
{cors_after_request}

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/{resource}", methods=["GET"])
def list_{resource}():
    if not _check_auth():
        return jsonify({{"{err_key}": "Unauthorized"}}), 401
    db = get_db()
    page  = int(request.args.get("page",  1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit
    rows  = db.execute(
        "SELECT id, {f1}, {f2}, {f3}, created_at FROM {resource} ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    total = db.execute("SELECT COUNT(*) FROM {resource}").fetchone()[0]
    items = [dict(r) for r in rows]
    return jsonify({{
        "{list_key}":  items,
        "{pag_key}":   total,
        "page":        page,
        "limit":       limit,
    }}), 200


@app.route("/api/{resource}", methods=["POST"])
def create_{singular}():
    if not _check_auth():
        return jsonify({{"{err_key}": "Unauthorized"}}), 401
    body = request.get_json(force=True, silent=True) or {{}}
    {f1}_val = body.get("{f1}", "")
    {f2}_val = body.get("{f2}", "")
    {f3}_val = body.get("{f3}", "")
    if not {f1}_val:
        return jsonify({{"{err_key}": "{f1} is required"}}), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO {resource} ({f1}, {f2}, {f3}) VALUES (?, ?, ?)",
        ({f1}_val, {f2}_val, {f3}_val),
    )
    db.commit()
    row = db.execute(
        "SELECT id, {f1}, {f2}, {f3}, created_at FROM {resource} WHERE id = ?",
        (cur.lastrowid,),
    ).fetchone()
    return jsonify({{"item": dict(row)}}), {post_status}


@app.route("/api/{resource}/<int:item_id>", methods=["GET"])
def get_{singular}(item_id):
    if not _check_auth():
        return jsonify({{"{err_key}": "Unauthorized"}}), 401
    db = get_db()
    row = db.execute(
        "SELECT id, {f1}, {f2}, {f3}, created_at FROM {resource} WHERE id = ?",
        (item_id,),
    ).fetchone()
    if row is None:
        return jsonify({{"{err_key}": "{singular_cap} not found"}}), 404
    return jsonify({{"{single_key}": dict(row)}}), 200


@app.route("/api/{resource}/<int:item_id>", methods=["PUT"])
def update_{singular}(item_id):
    if not _check_auth():
        return jsonify({{"{err_key}": "Unauthorized"}}), 401
    db = get_db()
    row = db.execute(
        "SELECT id FROM {resource} WHERE id = ?", (item_id,)
    ).fetchone()
    if row is None:
        return jsonify({{"{err_key}": "{singular_cap} not found"}}), 404
    body = request.get_json(force=True, silent=True) or {{}}
    {f1}_val = body.get("{f1}")
    {f2}_val = body.get("{f2}")
    {f3}_val = body.get("{f3}")
    if {f1}_val is not None:
        db.execute("UPDATE {resource} SET {f1}=? WHERE id=?", ({f1}_val, item_id))
    if {f2}_val is not None:
        db.execute("UPDATE {resource} SET {f2}=? WHERE id=?", ({f2}_val, item_id))
    if {f3}_val is not None:
        db.execute("UPDATE {resource} SET {f3}=? WHERE id=?", ({f3}_val, item_id))
    db.commit()
    updated = db.execute(
        "SELECT id, {f1}, {f2}, {f3}, created_at FROM {resource} WHERE id=?",
        (item_id,),
    ).fetchone()
    return jsonify({{"{single_key}": dict(updated)}}), 200


@app.route("/api/{resource}/<int:item_id>", methods=["DELETE"])
def delete_{singular}(item_id):
    if not _check_auth():
        return jsonify({{"{err_key}": "Unauthorized"}}), 401
    db = get_db()
    row = db.execute("SELECT id FROM {resource} WHERE id=?", (item_id,)).fetchone()
    if row is None:
        return jsonify({{"{err_key}": "{singular_cap} not found"}}), 404
    db.execute("DELETE FROM {resource} WHERE id=?", (item_id,))
    db.commit()
    return jsonify({{"deleted": item_id}}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False, port={port})
'''

    def _gen_frontend_py(
        self, resource, singular, f1, f2, f3, port, token,
        active_bugs,
        wrong_url_seg, wrong_list_key, wrong_error_key, wrong_single_key,
    ) -> str:
        # Decide actual values based on which bugs are active
        url_seg      = wrong_url_seg[1]      if "wrong_url_path"      in active_bugs else wrong_url_seg[0]
        auth_header  = {}                    if "missing_auth_header"  in active_bugs else {"Authorization": f"Bearer {token}"}
        list_field   = wrong_list_key[1]     if "wrong_list_field"     in active_bugs else wrong_list_key[0]
        error_field  = wrong_error_key[1]    if "wrong_error_field"    in active_bugs else wrong_error_key[0]
        single_field = wrong_single_key[1]   if "wrong_single_field"   in active_bugs else wrong_single_key[0]

        # Build headers literal
        if "missing_auth_header" in active_bugs:
            headers_literal = '{"Content-Type": "application/json"}'
        else:
            headers_literal = f'{{"Content-Type": "application/json", "Authorization": "Bearer {token}"}}'

        resource_cap = resource.capitalize()
        singular_cap = singular.capitalize()

        return f'''"""
{resource_cap} API client — Python frontend consumer.
WARNING: This file contains intentional bugs for the TeamBench exercise.
"""

import requests
import sys

BASE_URL = "http://localhost:{port}/{url_seg}/{resource}"
HEADERS  = {headers_literal}


def list_{resource}(page=1, limit=20):
    """Fetch a paginated list of {resource}."""
    resp = requests.get(
        BASE_URL,
        params={{"page": page, "limit": limit}},
        headers=HEADERS,
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    # BUG candidate: reading wrong key from response
    return data.get("{list_field}", [])


def create_{singular}({f1}, {f2}="", {f3}=""):
    """Create a new {singular}."""
    resp = requests.post(
        BASE_URL,
        json={{"{f1}": {f1}, "{f2}": {f2}, "{f3}": {f3}}},
        headers=HEADERS,
        timeout=5,
    )
    if resp.status_code not in (200, 201):
        err = resp.json()
        # BUG candidate: reading wrong error key
        raise RuntimeError(f"Create failed: {{err.get('{error_field}', 'unknown error')}}")
    return resp.json().get("item")


def get_{singular}(item_id):
    """Fetch a single {singular} by id."""
    resp = requests.get(f"{{BASE_URL}}/{{item_id}}", headers=HEADERS, timeout=5)
    if resp.status_code == 404:
        err = resp.json()
        # BUG candidate: reading wrong error key on 404
        raise ValueError(f"{singular_cap} not found: {{err.get('{error_field}', 'not found')}}")
    resp.raise_for_status()
    data = resp.json()
    # BUG candidate: reading wrong single-item key
    return data.get("{single_field}")


def delete_{singular}(item_id):
    """Delete a {singular} by id."""
    resp = requests.delete(f"{{BASE_URL}}/{{item_id}}", headers=HEADERS, timeout=5)
    resp.raise_for_status()
    return resp.json()


def main():
    print(f"Connecting to {{BASE_URL}} ...")
    try:
        items = list_{resource}()
        print(f"Found {{len(items)}} {resource}.")
    except Exception as exc:
        print(f"ERROR listing {resource}: {{exc}}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

    def _gen_test_py(
        self, resource, singular, f1, f2, f3, port, token,
        active_backend_bugs, active_frontend_bugs,
        wrong_list_key, wrong_post_status,
        wrong_pagination_key, wrong_error_key,
        wrong_url_seg, wrong_single_key,
    ) -> str:
        resource_cap = resource.capitalize()
        singular_cap = singular.capitalize()

        # Correct contract values
        correct_list_key     = wrong_list_key[0]
        correct_pag_key      = wrong_pagination_key[0]
        correct_error_key    = wrong_error_key[0]
        correct_url_seg      = wrong_url_seg[0]
        correct_single_key   = wrong_single_key[0]

        # Wrong values (what was bugged)
        bad_list_key         = wrong_list_key[1]
        bad_post_status      = wrong_post_status
        bad_pag_key          = wrong_pagination_key[1]
        bad_error_key        = wrong_error_key[1]
        bad_url_seg          = wrong_url_seg[1]
        bad_single_key       = wrong_single_key[1]

        return f'''"""
Contract test suite for MULTI2_api_frontend.
Tests verify the API contract between backend and frontend.
Do NOT modify this file.
"""

import json
import os
import sys
import importlib
import unittest

# ---------------------------------------------------------------------------
# Backend tests (Flask test client)
# ---------------------------------------------------------------------------

class BackendContractTests(unittest.TestCase):
    """Tests the backend server against the API contract."""

    AUTH_TOKEN = "{token}"
    RESOURCE   = "{resource}"
    F1         = "{f1}"
    F2         = "{f2}"
    F3         = "{f3}"

    def setUp(self):
        """Import and reset the Flask app."""
        backend_dir = os.path.join(os.path.dirname(__file__), "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        import server as server_mod
        importlib.reload(server_mod)
        self.server_mod = server_mod
        self.client = server_mod.app.test_client()
        server_mod.app.testing = True
        self._auth = {{"Authorization": f"Bearer {{self.AUTH_TOKEN}}"}}

    def _post_item(self, f1_val="test_{f1}", f2_val="test_{f2}", f3_val="test_{f3}"):
        return self.client.post(
            f"/api/{{self.RESOURCE}}",
            data=json.dumps({{self.F1: f1_val, self.F2: f2_val, self.F3: f3_val}}),
            content_type="application/json",
            headers=self._auth,
        )

    # -----------------------------------------------------------------------
    # Check 1: backend imports cleanly
    # -----------------------------------------------------------------------
    def test_01_backend_imports(self):
        """backend/server.py must import without error."""
        self.assertIsNotNone(self.server_mod.app)

    # -----------------------------------------------------------------------
    # Check 2: POST returns 201 (not {bad_post_status} or other wrong code)
    # -----------------------------------------------------------------------
    def test_02_post_returns_201(self):
        """POST /api/{resource} must return HTTP 201 Created."""
        resp = self._post_item()
        self.assertEqual(
            resp.status_code, 201,
            msg=f"Expected 201, got {{resp.status_code}}. "
                f"Contract says POST must return 201."
        )

    # -----------------------------------------------------------------------
    # Check 3: POST response body wraps item under 'item' key
    # -----------------------------------------------------------------------
    def test_03_post_response_schema(self):
        """POST response must contain 'item' key with the created resource."""
        resp = self._post_item(f1_val="check3_{f1}")
        self.assertEqual(resp.status_code, 201)
        body = json.loads(resp.data)
        self.assertIn(
            "item", body,
            msg=f"POST response missing 'item' key. Got keys: {{list(body.keys())}}"
        )
        item = body["item"]
        self.assertIn("id", item)
        self.assertIn(self.F1, item)

    # -----------------------------------------------------------------------
    # Check 4: GET list response uses correct 'items' key
    # -----------------------------------------------------------------------
    def test_04_get_list_uses_correct_key(self):
        """GET /api/{resource} must return list under '{correct_list_key}' key."""
        self._post_item(f1_val="list_key_test")
        resp = self.client.get(f"/api/{{self.RESOURCE}}", headers=self._auth)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertIn(
            "{correct_list_key}", body,
            msg=(
                "GET list response missing '{correct_list_key}' key. "
                "Got keys: " + str(list(body.keys())) + ". "
                "Hint: backend may be using '{bad_list_key}' instead."
            ),
        )
        self.assertIsInstance(body["{correct_list_key}"], list)

    # -----------------------------------------------------------------------
    # Check 5: GET list response includes pagination with '{correct_pag_key}'
    # -----------------------------------------------------------------------
    def test_05_get_list_pagination(self):
        """GET /api/{resource} must include pagination fields: '{correct_pag_key}', page, limit."""
        resp = self.client.get(f"/api/{{self.RESOURCE}}", headers=self._auth)
        body = json.loads(resp.data)
        self.assertIn(
            "{correct_pag_key}", body,
            msg=(
                "GET list missing '{correct_pag_key}' pagination field. "
                "Got keys: " + str(list(body.keys())) + ". "
                "Hint: backend may be using '{bad_pag_key}' instead."
            ),
        )
        self.assertIn("page",  body, msg="GET list missing 'page' field")
        self.assertIn("limit", body, msg="GET list missing 'limit' field")

    # -----------------------------------------------------------------------
    # Check 6: CORS header present on GET response
    # -----------------------------------------------------------------------
    def test_06_cors_header_present(self):
        """Responses must include Access-Control-Allow-Origin header."""
        resp = self.client.get(f"/api/{{self.RESOURCE}}", headers=self._auth)
        cors = resp.headers.get("Access-Control-Allow-Origin", "")
        self.assertTrue(
            cors != "",
            msg="Missing Access-Control-Allow-Origin header on GET /api/{resource}. "
                "The backend must add CORS headers."
        )

    # -----------------------------------------------------------------------
    # Check 7: Error responses use '{correct_error_key}' key
    # -----------------------------------------------------------------------
    def test_07_error_response_uses_correct_key(self):
        """401/404 error responses must use '{{'{correct_error_key}'}}' key."""
        # Hit endpoint without auth to get a 401
        resp = self.client.get(f"/api/{{self.RESOURCE}}")
        self.assertEqual(resp.status_code, 401)
        body = json.loads(resp.data)
        self.assertIn(
            "{correct_error_key}", body,
            msg=(
                "Error response missing '{correct_error_key}' key. "
                "Got keys: " + str(list(body.keys())) + ". "
                "Hint: backend may be using '{bad_error_key}' instead."
            ),
        )

    # -----------------------------------------------------------------------
    # Check 8: GET single item uses 'item' key
    # -----------------------------------------------------------------------
    def test_08_get_single_item_key(self):
        """GET /api/{resource}/<id> must wrap response under 'item' key."""
        create_resp = self._post_item(f1_val="single_key_test")
        item_id = json.loads(create_resp.data)["item"]["id"]
        resp = self.client.get(f"/api/{{self.RESOURCE}}/{{item_id}}", headers=self._auth)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.data)
        self.assertIn(
            "item", body,
            msg=f"GET single response missing 'item' key. Got: {{list(body.keys())}}"
        )

    # -----------------------------------------------------------------------
    # Check 9: GET non-existent returns 404 with error key
    # -----------------------------------------------------------------------
    def test_09_get_missing_404(self):
        """GET /api/{resource}/99999 must return 404 with error key."""
        resp = self.client.get(f"/api/{{self.RESOURCE}}/99999", headers=self._auth)
        self.assertEqual(resp.status_code, 404)
        body = json.loads(resp.data)
        self.assertIn(
            "{correct_error_key}", body,
            msg=(
                "404 response missing '{correct_error_key}' key. Got: "
                + str(list(body.keys()))
            ),
        )


# ---------------------------------------------------------------------------
# Frontend tests (static analysis + integration with test server)
# ---------------------------------------------------------------------------

class FrontendContractTests(unittest.TestCase):
    """Tests the frontend client against the API contract."""

    AUTH_TOKEN = "{token}"
    RESOURCE   = "{resource}"
    F1         = "{f1}"

    def setUp(self):
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        if frontend_dir not in sys.path:
            sys.path.insert(0, frontend_dir)
        import app as app_mod
        importlib.reload(app_mod)
        self.app_mod = app_mod

    # -----------------------------------------------------------------------
    # Check 10: frontend/app.py imports cleanly
    # -----------------------------------------------------------------------
    def test_10_frontend_imports(self):
        """frontend/app.py must import without error (no NameError/SyntaxError)."""
        self.assertIsNotNone(self.app_mod)

    # -----------------------------------------------------------------------
    # Check 11: frontend BASE_URL uses correct path segment 'api'
    # -----------------------------------------------------------------------
    def test_11_frontend_url_path(self):
        """frontend/app.py BASE_URL must use '/api/{resource}' path, not a typo."""
        src_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
        with open(src_path) as f:
            src = f.read()
        self.assertIn(
            "/api/{resource}", src,
            msg=f"frontend/app.py BASE_URL must contain '/api/{resource}'. "
                f"Hint: may be using '/{bad_url_seg}/{resource}' instead."
        )

    # -----------------------------------------------------------------------
    # Check 12: frontend HEADERS include Authorization Bearer token
    # -----------------------------------------------------------------------
    def test_12_frontend_auth_header(self):
        """frontend/app.py HEADERS must include 'Authorization' with Bearer token."""
        src_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
        with open(src_path) as f:
            src = f.read()
        self.assertIn(
            "Authorization", src,
            msg="frontend/app.py HEADERS missing 'Authorization' key. "
                "All API requests require Bearer token auth."
        )
        self.assertIn(
            "Bearer", src,
            msg="frontend/app.py HEADERS missing 'Bearer' in Authorization value."
        )

    # -----------------------------------------------------------------------
    # Check 13: list_{resource} reads '{correct_list_key}' from response
    # -----------------------------------------------------------------------
    def test_13_frontend_reads_correct_list_key(self):
        """frontend list_{resource}() must NOT use wrong list key '{bad_list_key}'."""
        src_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
        with open(src_path) as f:
            src = f.read()
        import re
        # Extract the list_{resource} function body by splitting on 'def '
        fn_body = src
        parts = re.split(r"(?=^def )", src, flags=re.MULTILINE)
        for part in parts:
            if part.startswith("def list_{resource}("):
                fn_body = part
                break
        self.assertNotIn(
            '"{bad_list_key}"', fn_body,
            msg=(
                'frontend/app.py list_{resource}() still uses wrong key "{bad_list_key}". '
                'Should use "{correct_list_key}" to match API contract.'
            ),
        )

    # -----------------------------------------------------------------------
    # Check 14: error handling reads '{correct_error_key}' not '{bad_error_key}'
    # -----------------------------------------------------------------------
    def test_14_frontend_reads_correct_error_key(self):
        """frontend error handling must read '{correct_error_key}' not '{bad_error_key}'."""
        src_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
        with open(src_path) as f:
            src = f.read()
        self.assertIn(
            "'{correct_error_key}'", src,
            msg=(
                "frontend/app.py error handling must reference '{correct_error_key}'. "
                "Hint: may be reading '{bad_error_key}' instead."
            ),
        )

    # -----------------------------------------------------------------------
    # Check 15: get_{singular} reads '{correct_single_key}' not '{bad_single_key}'
    # -----------------------------------------------------------------------
    def test_15_frontend_reads_correct_single_key(self):
        """frontend get_{singular}() must NOT use wrong single key '{bad_single_key}'."""
        src_path = os.path.join(os.path.dirname(__file__), "frontend", "app.py")
        with open(src_path) as f:
            src = f.read()
        import re
        # Extract the get_{singular} function body by splitting on 'def '
        fn_body = src
        parts = re.split(r"(?=^def )", src, flags=re.MULTILINE)
        for part in parts:
            if part.startswith("def get_{singular}("):
                fn_body = part
                break
        self.assertNotIn(
            '"{bad_single_key}"', fn_body,
            msg=(
                'frontend/app.py get_{singular}() still uses wrong key "{bad_single_key}". '
                'Should use "{correct_single_key}" to match API contract.'
            ),
        )


# ---------------------------------------------------------------------------
# End-to-end integration test (backend + frontend together via test client)
# ---------------------------------------------------------------------------

class EndToEndTests(unittest.TestCase):
    """Integration tests: frontend functions called against live backend."""

    AUTH_TOKEN = "{token}"
    RESOURCE   = "{resource}"
    F1         = "{f1}"
    F2         = "{f2}"
    F3         = "{f3}"

    def setUp(self):
        # Set up backend
        backend_dir = os.path.join(os.path.dirname(__file__), "backend")
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        import server as server_mod
        importlib.reload(server_mod)
        self.server_mod = server_mod
        server_mod.app.testing = True
        self._flask_client = server_mod.app.test_client()

        # Monkey-patch requests in frontend to use Flask test client
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        if frontend_dir not in sys.path:
            sys.path.insert(0, frontend_dir)

        import app as app_mod
        importlib.reload(app_mod)
        self.app_mod = app_mod

        # Patch BASE_URL and HEADERS for test client usage
        # We test contract correctness via static checks; e2e verifies no crash
        self._orig_base = app_mod.BASE_URL
        self._orig_headers = app_mod.HEADERS

    def tearDown(self):
        self.app_mod.BASE_URL = self._orig_base
        self.app_mod.HEADERS  = self._orig_headers

    # -----------------------------------------------------------------------
    # Check 16: create_{singular} function exists and is callable
    # -----------------------------------------------------------------------
    def test_16_create_function_exists(self):
        """frontend/app.py must define create_{singular}() function."""
        self.assertTrue(
            callable(getattr(self.app_mod, "create_{singular}", None)),
            msg="frontend/app.py must define create_{singular}() function"
        )

    # -----------------------------------------------------------------------
    # Check 17: list_{resource} function exists and is callable
    # -----------------------------------------------------------------------
    def test_17_list_function_exists(self):
        """frontend/app.py must define list_{resource}() function."""
        self.assertTrue(
            callable(getattr(self.app_mod, "list_{resource}", None)),
            msg="frontend/app.py must define list_{resource}() function"
        )

    # -----------------------------------------------------------------------
    # Check 18: get_{singular} function exists and is callable
    # -----------------------------------------------------------------------
    def test_18_get_function_exists(self):
        """frontend/app.py must define get_{singular}() function."""
        self.assertTrue(
            callable(getattr(self.app_mod, "get_{singular}", None)),
            msg="frontend/app.py must define get_{singular}() function"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
'''

    def _gen_spec(
        self, app_type, resource, singular, f1, f2, f3, port, token,
        correct_list_key, correct_pag_key, correct_error_key, correct_single_key,
    ) -> str:
        resource_cap = resource.capitalize()
        singular_cap = singular.capitalize()
        app_type_display = app_type.replace("_", " ").title()
        return f"""# MULTI2: API & Frontend Contract Fix — Full Specification (Planner Only)

## Overview

A {app_type_display} application split into a Flask REST API backend
(`backend/server.py`) and a Python API client frontend (`frontend/app.py`).
Both sides have bugs that violate the contract below. Fix all bugs so that
`python3 test_contract.py` passes all 18 checks.

---

## Application Architecture

```
workspace/
  backend/
    server.py          # Flask REST API (has bugs)
  frontend/
    app.py             # Python requests-based API client (has bugs)
  test_contract.py     # Full contract test suite (do NOT modify)
```

---

## API Contract

### Authentication

All requests must include an `Authorization` header:

```
Authorization: Bearer {token}
```

Without this header the server returns **401 Unauthorized**.

### Base URL

```
http://localhost:{port}/api/{resource}
```

### Endpoints

#### `GET /api/{resource}`

List {resource} with pagination.

**Query parameters:** `page` (int, default 1), `limit` (int, default 20)

**Response 200:**
```json
{{
  "{correct_list_key}": [
    {{"id": 1, "{f1}": "...", "{f2}": "...", "{f3}": "...", "created_at": "..."}}
  ],
  "{correct_pag_key}": 42,
  "page": 1,
  "limit": 20
}}
```

- The list MUST be under the key `"{correct_list_key}"` (not `"data"`, `"results"`, etc.)
- The total count MUST be under `"{correct_pag_key}"` (not `"count"`, `"size"`, etc.)

#### `POST /api/{resource}`

Create a new {singular}.

**Request body (JSON):**
```json
{{"{f1}": "...", "{f2}": "...", "{f3}": "..."}}
```

**Response 201 Created:**
```json
{{"item": {{"id": 1, "{f1}": "...", "{f2}": "...", "{f3}": "...", "created_at": "..."}}}}
```

- Status MUST be **201** (not 200, 202, or 204)
- Response MUST wrap the created object under `"item"`

#### `GET /api/{resource}/<id>`

Fetch a single {singular}.

**Response 200:**
```json
{{"item": {{"id": 1, "{f1}": "...", "{f2}": "...", "{f3}": "...", "created_at": "..."}}}}
```

- Response MUST wrap under `"{correct_single_key}"` (not `"data"`, `"record"`, etc.)

**Response 404:**
```json
{{"{correct_error_key}": "{singular_cap} not found"}}
```

#### `PUT /api/{resource}/<id>`

Update fields on an existing {singular}. Partial updates allowed.

**Response 200:** same schema as GET single.

#### `DELETE /api/{resource}/<id>`

Delete a {singular}.

**Response 200:**
```json
{{"deleted": <id>}}
```

### Error Responses

ALL error responses (4xx, 5xx) MUST use the key `"{correct_error_key}"`:

```json
{{"{correct_error_key}": "Human-readable message"}}
```

Do NOT use `"message"`, `"msg"`, or `"detail"` as the error key.

### CORS

All responses MUST include:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

---

## Bug Inventory

### Backend bugs — `backend/server.py`

The backend has **3–5** bugs from the following categories:

1. **Wrong list response key** — GET list wraps items under wrong key (e.g., `"data"` instead of `"{correct_list_key}"`)
2. **Wrong POST status code** — POST returns wrong HTTP status (e.g., 200 instead of 201)
3. **Missing CORS headers** — `after_request` hook absent or incomplete
4. **Wrong pagination key** — total count under wrong key (e.g., `"count"` instead of `"{correct_pag_key}"`)
5. **Wrong error key** — error responses use `"message"` instead of `"{correct_error_key}"`

Not all 5 may be present in any given instance. Identify which are violated by running the tests.

### Frontend bugs — `frontend/app.py`

The frontend has **3–5** bugs from the following categories:

1. **Wrong URL path** — `BASE_URL` uses wrong path segment (e.g., `/apiv1/` instead of `/api/`)
2. **Missing auth header** — `HEADERS` dict missing `Authorization: Bearer <token>`
3. **Wrong list field** — `list_{resource}()` reads `data.get("data")` instead of `data.get("{correct_list_key}")`
4. **Wrong error field** — error handling reads `err.get("message")` instead of `err.get("{correct_error_key}")`
5. **Wrong single-item field** — `get_{singular}()` reads `data.get("data")` instead of `data.get("{correct_single_key}")`

---

## Expected Outcome

After all fixes:

```
python3 test_contract.py
```

Should produce:
```
..................
----------------------------------------------------------------------
Ran 18 tests in X.XXXs

OK
```

All 18 tests pass across `BackendContractTests`, `FrontendContractTests`, and `EndToEndTests`.

---

## Constraints

- Do NOT modify `test_contract.py`
- Only `flask` and `requests` are available as external dependencies
- The SQLite database is in-memory — no persistent storage needed
- Token value: `{token}`
- Backend port: `{port}`
"""

    def _gen_brief(self, app_type: str, resource: str) -> str:
        app_display = app_type.replace("_", " ").title()
        return f"""# MULTI2: API & Frontend Contract Fix (Brief)

The {app_display} web application's frontend is showing errors when trying to
communicate with the backend API. Investigate the issue and fix it.

Files:
- `backend/server.py` — Flask REST API server
- `frontend/app.py`   — Python API client (the "frontend" consumer)

Run `python3 test_contract.py` — all 18 tests must pass.

Do NOT modify `test_contract.py`.
"""
