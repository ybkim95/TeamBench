"""
Parameterized generator for API1: API Version Compatibility.

Each seed produces a different service domain
(users / products / orders / reports / auth) with a Flask API being
upgraded from v1 to v2:

  3 endpoints need backward-compatible v1 shims (must add/keep):
    E1. renamed_field:      v2 renames a response field; v1 shim maps old name -> new
    E2. restructured_resp:  v2 restructures the response shape; v1 shim flattens it back
    E3. added_required:     v2 adds a required request param; v1 shim supplies default

  1 endpoint must NOT have a v1 shim (security fix — old behavior must be rejected):
    E4. security_break:     v1 allowed unauthenticated access; v2 enforces auth;
                            returning v1 behavior would be a security regression

  1 endpoint's v1 shim should be REMOVED (clients have already migrated):
    E5. stale_shim:         v1 shim exists in the codebase but is now dead code;
                            the compatibility matrix says to remove it

Information asymmetry (TNI pattern A):
  spec.md   — compatibility matrix documenting which endpoints need shims / no-shim / remove
  brief.md  — "add v2 endpoints while maintaining v1 compatibility" (no specifics)

Grade: send v1 and v2 HTTP requests and verify correct responses for each endpoint.
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom


# ── Domain configurations ──────────────────────────────────────────────────────

DOMAINS = [
    {
        "name": "users",
        "service": "UserService",
        "module": "app",
        "resource": "user",
        "resource_plural": "users",
        "id_field": "user_id",
        # E1: field rename
        "e1_path": "/users/<int:uid>",
        "e1_name": "get_user",
        "e1_v1_field": "full_name",
        "e1_v2_field": "display_name",
        "e1_desc": "Get user profile",
        # E2: response restructure
        "e2_path": "/users/<int:uid>/preferences",
        "e2_name": "get_preferences",
        "e2_v1_shape": '{"theme": "dark", "lang": "en"}',
        "e2_v2_shape": '{"preferences": {"theme": "dark", "lang": "en"}, "version": 2}',
        "e2_desc": "Get user preferences",
        # E3: added required param
        "e3_path": "/users/search",
        "e3_name": "search_users",
        "e3_v2_param": "page",
        "e3_v1_default": "1",
        "e3_desc": "Search users",
        # E4: security break (no shim)
        "e4_path": "/users/<int:uid>/tokens",
        "e4_name": "get_tokens",
        "e4_security_note": "v1 returned tokens without auth check; v2 requires Bearer token",
        "e4_desc": "Get user tokens (auth required)",
        # E5: stale shim to remove
        "e5_path": "/users/legacy_export",
        "e5_name": "legacy_export",
        "e5_stale_reason": "All clients migrated to /v2/users/export by 2025-Q1",
        "e5_desc": "Legacy export endpoint",
    },
    {
        "name": "products",
        "service": "ProductService",
        "module": "app",
        "resource": "product",
        "resource_plural": "products",
        "id_field": "product_id",
        "e1_path": "/products/<int:pid>",
        "e1_name": "get_product",
        "e1_v1_field": "product_name",
        "e1_v2_field": "title",
        "e1_desc": "Get product details",
        "e2_path": "/products/<int:pid>/pricing",
        "e2_name": "get_pricing",
        "e2_v1_shape": '{"price": 9.99, "currency": "USD"}',
        "e2_v2_shape": '{"pricing": {"amount": 9.99, "currency": "USD"}, "tax_included": false}',
        "e2_desc": "Get product pricing",
        "e3_path": "/products/search",
        "e3_name": "search_products",
        "e3_v2_param": "limit",
        "e3_v1_default": "20",
        "e3_desc": "Search products",
        "e4_path": "/products/<int:pid>/inventory",
        "e4_name": "get_inventory",
        "e4_security_note": "v1 exposed stock counts publicly; v2 requires warehouse role",
        "e4_desc": "Get inventory levels (warehouse role required)",
        "e5_path": "/products/v1_bulk",
        "e5_name": "v1_bulk",
        "e5_stale_reason": "Bulk import clients migrated to /v2/products/import in 2024-Q4",
        "e5_desc": "Legacy bulk import endpoint",
    },
    {
        "name": "orders",
        "service": "OrderService",
        "module": "app",
        "resource": "order",
        "resource_plural": "orders",
        "id_field": "order_id",
        "e1_path": "/orders/<int:oid>",
        "e1_name": "get_order",
        "e1_v1_field": "status",
        "e1_v2_field": "order_status",
        "e1_desc": "Get order details",
        "e2_path": "/orders/<int:oid>/items",
        "e2_name": "get_order_items",
        "e2_v1_shape": '[{"sku": "X1", "qty": 2}]',
        "e2_v2_shape": '{"items": [{"sku": "X1", "quantity": 2}], "total_items": 1}',
        "e2_desc": "Get order line items",
        "e3_path": "/orders/history",
        "e3_name": "get_order_history",
        "e3_v2_param": "from_date",
        "e3_v1_default": "1970-01-01",
        "e3_desc": "Get order history",
        "e4_path": "/orders/<int:oid>/cancel",
        "e4_name": "cancel_order",
        "e4_security_note": "v1 allowed any user to cancel any order; v2 requires ownership check",
        "e4_desc": "Cancel order (owner or admin required)",
        "e5_path": "/orders/legacy_status",
        "e5_name": "legacy_status",
        "e5_stale_reason": "Status polling clients replaced by webhook integration in 2025-Q2",
        "e5_desc": "Legacy status polling endpoint",
    },
    {
        "name": "reports",
        "service": "ReportService",
        "module": "app",
        "resource": "report",
        "resource_plural": "reports",
        "id_field": "report_id",
        "e1_path": "/reports/<int:rid>",
        "e1_name": "get_report",
        "e1_v1_field": "created",
        "e1_v2_field": "created_at",
        "e1_desc": "Get report metadata",
        "e2_path": "/reports/<int:rid>/summary",
        "e2_name": "get_summary",
        "e2_v1_shape": '{"total": 42, "avg": 7.0}',
        "e2_v2_shape": '{"summary": {"total": 42, "average": 7.0}, "computed_at": "2025-01-01T00:00:00Z"}',
        "e2_desc": "Get report summary",
        "e3_path": "/reports/list",
        "e3_name": "list_reports",
        "e3_v2_param": "format",
        "e3_v1_default": "json",
        "e3_desc": "List available reports",
        "e4_path": "/reports/<int:rid>/raw",
        "e4_name": "get_raw_data",
        "e4_security_note": "v1 returned raw data without PII masking; v2 enforces data classification",
        "e4_desc": "Get raw report data (data-owner role required)",
        "e5_path": "/reports/v1_download",
        "e5_name": "v1_download",
        "e5_stale_reason": "Download clients migrated to /v2/reports/export after PDF support added",
        "e5_desc": "Legacy download endpoint",
    },
    {
        "name": "auth",
        "service": "AuthService",
        "module": "app",
        "resource": "session",
        "resource_plural": "sessions",
        "id_field": "session_id",
        "e1_path": "/auth/session/<string:sid>",
        "e1_name": "get_session",
        "e1_v1_field": "user",
        "e1_v2_field": "subject",
        "e1_desc": "Get session details",
        "e2_path": "/auth/session/<string:sid>/claims",
        "e2_name": "get_claims",
        "e2_v1_shape": '{"roles": ["admin"], "exp": 9999999999}',
        "e2_v2_shape": '{"claims": {"roles": ["admin"]}, "expires_at": "2286-11-20T17:46:39Z"}',
        "e2_desc": "Get session claims",
        "e3_path": "/auth/verify",
        "e3_name": "verify_token",
        "e3_v2_param": "audience",
        "e3_v1_default": "default",
        "e3_desc": "Verify a token",
        "e4_path": "/auth/admin/sessions",
        "e4_name": "list_all_sessions",
        "e4_security_note": "v1 listed all sessions without privilege check; v2 requires admin role",
        "e4_desc": "List all sessions (admin role required)",
        "e5_path": "/auth/legacy_login",
        "e5_name": "legacy_login",
        "e5_stale_reason": "Basic-auth login clients migrated to OAuth2 flow in 2024-Q3",
        "e5_desc": "Legacy basic-auth login endpoint",
    },
]


class Generator(TaskGenerator):
    task_id = "API1_version_compat"
    domain = "API Design"
    difficulty = "hard"
    languages = ["python"]

    @staticmethod
    def _clean(s: str) -> str:
        return textwrap.dedent(s).strip() + "\n"

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain_idx = seed % len(DOMAINS)
        cfg = DOMAINS[domain_idx]

        # Seed-parameterized variant values
        port = rng.choice([5000, 5001, 5002, 8000, 8080])
        api_prefix = rng.choice(["/api", "/service", "/v"])

        workspace_files = self._make_workspace(cfg, port)
        spec_md = self._clean(self._make_spec(cfg))
        brief_md = self._clean(self._make_brief(cfg))

        return GeneratedTask(
            task_id="API1_version_compat",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected={
                "seed": seed,
                "domain": cfg["name"],
                "port": port,
                "shim_endpoints": ["e1_renamed_field", "e2_restructured_resp", "e3_added_required"],
                "no_shim_endpoint": "e4_security_break",
                "remove_shim_endpoint": "e5_stale_shim",
                "e1_v1_field": cfg["e1_v1_field"],
                "e1_v2_field": cfg["e1_v2_field"],
                "e3_v2_param": cfg["e3_v2_param"],
                "e3_v1_default": cfg["e3_v1_default"],
                "checks_total": 10,
            },
            workspace_files=workspace_files,
            metadata={"difficulty": "hard", "category": "API Design"},
        )

    # ── Workspace file generators ──────────────────────────────────────────────

    def _make_workspace(self, cfg: dict, port: int) -> dict:
        files: dict = {}
        files["app.py"] = self._make_app(cfg, port)
        files["compat_matrix.md"] = self._make_compat_matrix(cfg)
        files["tests/test_v1_compat.py"] = self._make_v1_tests(cfg, port)
        files["tests/test_v2_endpoints.py"] = self._make_v2_tests(cfg, port)
        files["requirements.txt"] = "flask>=2.3\npytest\nrequests\n"
        files["README.md"] = self._make_readme(cfg, port)
        return files

    def _make_app(self, cfg: dict, port: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"
            {c['service']}: Flask API with v1/v2 versioning.

            v2 endpoints are the canonical implementation.
            Some v1 routes need backward-compatibility shims.
            See compat_matrix.md for which endpoints need shims, no-shim, or removal.
            \"\"\"
            from __future__ import annotations

            from flask import Flask, jsonify, request, abort

            app = Flask(__name__)

            # ── Seed data (in-memory for testing) ─────────────────────────────────────────
            SEED_DATA = {{
                1: {{
                    "{c['id_field']}": 1,
                    "{c['e1_v2_field']}": "Sample {c['resource'].capitalize()} One",
                    "active": True,
                    "meta": {{"created_at": "2025-01-01T00:00:00Z"}},
                }},
                2: {{
                    "{c['id_field']}": 2,
                    "{c['e1_v2_field']}": "Sample {c['resource'].capitalize()} Two",
                    "active": True,
                    "meta": {{"created_at": "2025-02-01T00:00:00Z"}},
                }},
            }}


            # ════════════════════════════════════════════════════════════════════════════
            # v2 endpoints — canonical implementation
            # ════════════════════════════════════════════════════════════════════════════

            # E1 v2: {c['e1_desc']} — uses new field name `{c['e1_v2_field']}`
            @app.route("/v2{c['e1_path']}")
            def v2_{c['e1_name']}(uid=None, pid=None, oid=None, rid=None, sid=None):
                item_id = uid or pid or oid or rid or sid or 1
                item = SEED_DATA.get(int(str(item_id)), SEED_DATA[1])
                return jsonify({{
                    "{c['id_field']}": item["{c['id_field']}"],
                    "{c['e1_v2_field']}": item["{c['e1_v2_field']}"],
                    "active": item["active"],
                }})


            # E2 v2: {c['e2_desc']} — uses nested response shape
            @app.route("/v2{c['e2_path']}")
            def v2_{c['e2_name']}(uid=None, pid=None, oid=None, rid=None, sid=None):
                return jsonify({c['e2_v2_shape']})


            # E3 v2: {c['e3_desc']} — requires `{c['e3_v2_param']}` parameter
            @app.route("/v2{c['e3_path']}")
            def v2_{c['e3_name']}():
                param = request.args.get("{c['e3_v2_param']}")
                if param is None:
                    abort(400, description="Missing required parameter: {c['e3_v2_param']}")
                q = request.args.get("q", "")
                return jsonify({{
                    "results": [v for v in SEED_DATA.values()
                                if q.lower() in str(v).lower()],
                    "{c['e3_v2_param']}": param,
                }})


            # E4 v2: {c['e4_desc']} — enforces authentication
            @app.route("/v2{c['e4_path']}")
            def v2_{c['e4_name']}(uid=None, pid=None, oid=None, rid=None, sid=None):
                auth = request.headers.get("Authorization", "")
                if not auth.startswith("Bearer "):
                    abort(401, description="Authentication required")
                return jsonify({{"data": [], "authenticated": True}})


            # E5 v2 replacement: canonical new endpoint
            @app.route("/v2/{c['resource_plural']}/export")
            def v2_export():
                return jsonify({{"export": list(SEED_DATA.values()), "format": "v2"}})


            # ════════════════════════════════════════════════════════════════════════════
            # v1 backward-compatibility shims
            # Status: INCOMPLETE — see compat_matrix.md for what needs to be done
            # ════════════════════════════════════════════════════════════════════════════

            # TODO E1: Add v1 shim for {c['e1_path']} that maps `{c['e1_v2_field']}` -> `{c['e1_v1_field']}`
            # @app.route("/v1{c['e1_path']}")
            # def v1_{c['e1_name']}(...):
            #     ...


            # TODO E2: Add v1 shim for {c['e2_path']} that flattens nested response back to v1 shape
            # @app.route("/v1{c['e2_path']}")
            # def v1_{c['e2_name']}(...):
            #     ...


            # TODO E3: Add v1 shim for {c['e3_path']} that supplies default for `{c['e3_v2_param']}`
            # @app.route("/v1{c['e3_path']}")
            # def v1_{c['e3_name']}():
            #     ...


            # E4: NO v1 shim — {c['e4_security_note']}.
            # A v1 shim here would be a security regression. Do NOT add one.


            # E5: STALE shim — remove this route (all clients have migrated)
            @app.route("/v1{c['e5_path']}")
            def v1_{c['e5_name']}():
                \"\"\"STALE: {c['e5_stale_reason']}. Remove this route.\"\"\";
                return jsonify({{"data": [], "legacy": True}})


            if __name__ == "__main__":
                app.run(port={port}, debug=False)
            """)

    def _make_compat_matrix(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # API Compatibility Matrix — {c['service']}

            ## Overview

            This matrix documents the v1 -> v2 migration status for all {c['service']}
            endpoints. It is the authoritative reference for compatibility decisions.

            ## Endpoints

            | Endpoint | v1 Path | v2 Path | Action | Reason |
            |----------|---------|---------|--------|--------|
            | E1 ({c['e1_name']}) | `/v1{c['e1_path']}` | `/v2{c['e1_path']}` | **ADD shim** | v2 renames `{c['e1_v1_field']}` -> `{c['e1_v2_field']}` |
            | E2 ({c['e2_name']}) | `/v1{c['e2_path']}` | `/v2{c['e2_path']}` | **ADD shim** | v2 restructures response into nested shape |
            | E3 ({c['e3_name']}) | `/v1{c['e3_path']}` | `/v2{c['e3_path']}` | **ADD shim** | v2 requires `{c['e3_v2_param']}` param; v1 clients don't send it |
            | E4 ({c['e4_name']}) | _(none)_ | `/v2{c['e4_path']}` | **NO shim** | Security fix: {c['e4_security_note']} |
            | E5 ({c['e5_name']}) | `/v1{c['e5_path']}` | `/v2/{c['resource_plural']}/export` | **REMOVE shim** | {c['e5_stale_reason']} |

            ## Shim Specifications

            ### E1 — Field Rename Shim

            v1 clients expect `{c['e1_v1_field']}` in the response.
            v2 returns `{c['e1_v2_field']}`.

            The v1 shim at `/v1{c['e1_path']}` must:
            1. Call the v2 handler (or duplicate its logic)
            2. Rename `{c['e1_v2_field']}` -> `{c['e1_v1_field']}` in the response

            ### E2 — Response Restructure Shim

            v1 clients expect a flat response: `{c['e2_v1_shape']}`
            v2 returns a nested response: `{c['e2_v2_shape']}`

            The v1 shim at `/v1{c['e2_path']}` must flatten the v2 response back to v1 shape.

            ### E3 — Added Required Parameter Shim

            v2 requires `{c['e3_v2_param']}` in the query string.
            v1 clients do not send this parameter.

            The v1 shim at `/v1{c['e3_path']}` must:
            1. Inject `{c['e3_v2_param']}={c['e3_v1_default']}` as the default when absent
            2. Forward the request to the v2 handler

            ### E4 — No Shim (Security Break)

            `/v2{c['e4_path']}` enforces authentication.
            **Do NOT create a `/v1{c['e4_path']}` shim.**
            {c['e4_security_note']}.
            Adding a shim here would silently re-introduce a security vulnerability.

            ### E5 — Remove Stale Shim

            `/v1{c['e5_path']}` currently exists in the codebase but is dead code.
            {c['e5_stale_reason']}.
            **Remove the `/v1{c['e5_path']}` route entirely.**

            ## Migration Status

            - E1, E2, E3: v1 shims missing — clients still on v1 routes will get 404
            - E4: correctly has no v1 shim
            - E5: v1 shim present but should be removed (dead code, maintenance burden)
            """)

    def _make_v1_tests(self, cfg: dict, port: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"Tests that v1 backward-compatibility shims work correctly.\"\"\";
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

            import pytest
            from app import app as flask_app


            @pytest.fixture
            def client():
                flask_app.config["TESTING"] = True
                with flask_app.test_client() as c:
                    yield c


            class TestV1Shims:
                def test_e1_v1_uses_old_field_name(self, client):
                    \"\"\"v1 response must use `{c['e1_v1_field']}`, not `{c['e1_v2_field']}`.\"\"\";
                    resp = client.get("/v1{c['e1_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 200
                    data = resp.get_json()
                    assert "{c['e1_v1_field']}" in data, "v1 response must contain '{c['e1_v1_field']}'"
                    assert "{c['e1_v2_field']}" not in data, "v1 response must NOT contain '{c['e1_v2_field']}'"

                def test_e2_v1_flat_response(self, client):
                    \"\"\"v1 response must be flat (v1 shape), not nested (v2 shape).\"\"\";
                    resp = client.get("/v1{c['e2_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 200
                    data = resp.get_json()
                    # v1 shape is flat — must NOT have nested wrapper key
                    nested_keys = [k for k, v in data.items() if isinstance(v, dict)]
                    assert len(nested_keys) == 0, f"v1 response must be flat, got nested keys: {{nested_keys}}"

                def test_e3_v1_no_param_required(self, client):
                    \"\"\"v1 search must work without `{c['e3_v2_param']}` parameter.\"\"\";
                    resp = client.get("/v1{c['e3_path']}")
                    assert resp.status_code == 200, (
                        "v1 search must not require '{c['e3_v2_param']}' parameter"
                    )

                def test_e4_no_v1_shim(self, client):
                    \"\"\"v1 path for E4 must NOT exist (security fix).\"\"\";
                    resp = client.get("/v1{c['e4_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 404, (
                        "/v1{c['e4_path']} must not exist (security: {c['e4_security_note']})"
                    )

                def test_e5_stale_shim_removed(self, client):
                    \"\"\"Stale v1 shim must be removed.\"\"\";
                    resp = client.get("/v1{c['e5_path']}")
                    assert resp.status_code == 404, (
                        "/v1{c['e5_path']} must be removed ({c['e5_stale_reason']})"
                    )
            """)

    def _make_v2_tests(self, cfg: dict, port: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            \"\"\"Tests that v2 endpoints still work correctly after changes.\"\"\";
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

            import pytest
            from app import app as flask_app


            @pytest.fixture
            def client():
                flask_app.config["TESTING"] = True
                with flask_app.test_client() as c:
                    yield c


            class TestV2Endpoints:
                def test_e1_v2_uses_new_field(self, client):
                    resp = client.get("/v2{c['e1_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 200
                    data = resp.get_json()
                    assert "{c['e1_v2_field']}" in data

                def test_e2_v2_nested_response(self, client):
                    resp = client.get("/v2{c['e2_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 200

                def test_e3_v2_requires_param(self, client):
                    resp = client.get("/v2{c['e3_path']}")
                    assert resp.status_code == 400, "v2 must require '{c['e3_v2_param']}'"

                def test_e3_v2_with_param(self, client):
                    resp = client.get(f"/v2{c['e3_path']}?{c['e3_v2_param']}={c['e3_v1_default']}")
                    assert resp.status_code == 200

                def test_e4_v2_requires_auth(self, client):
                    resp = client.get("/v2{c['e4_path']}".replace("<int:uid>", "1")
                                                          .replace("<int:pid>", "1")
                                                          .replace("<int:oid>", "1")
                                                          .replace("<int:rid>", "1")
                                                          .replace("<string:sid>", "abc"))
                    assert resp.status_code == 401

                def test_e4_v2_with_auth(self, client):
                    resp = client.get(
                        "/v2{c['e4_path']}".replace("<int:uid>", "1")
                                            .replace("<int:pid>", "1")
                                            .replace("<int:oid>", "1")
                                            .replace("<int:rid>", "1")
                                            .replace("<string:sid>", "abc"),
                        headers={{"Authorization": "Bearer test-token"}},
                    )
                    assert resp.status_code == 200
            """)

    def _make_readme(self, cfg: dict, port: int) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # {c['service']} — README

            Flask API service with v1/v2 versioning.

            ## Running

            ```bash
            pip install -r requirements.txt
            python app.py  # runs on port {port}
            ```

            ## Testing

            ```bash
            python -m pytest tests/ -v
            ```

            ## API Versions

            - v1: `/v1/...` — legacy, backward-compatible
            - v2: `/v2/...` — canonical, current

            See `compat_matrix.md` for the migration status of each endpoint.

            ## Notes

            - Only modify `app.py`
            - All tests must pass after changes
            """)

    # ── Spec / Brief generators ────────────────────────────────────────────────

    def _make_spec(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # API1_version_compat: API Version Compatibility — Full Specification (Planner Only)

            ## Overview

            The workspace contains `app.py` — a Flask {c['service']} being upgraded from v1 to v2.
            **3 endpoints need backward-compatible v1 shims** (add them),
            **1 endpoint must NOT have a shim** (security fix),
            **1 endpoint's shim must be removed** (clients have migrated).

            The executor only receives the brief. This spec provides the full compatibility analysis.

            ## File Structure

            - `app.py` — the ONLY file to modify
            - `compat_matrix.md` — compatibility matrix (authoritative reference, do not modify)
            - `tests/test_v1_compat.py` — v1 compatibility tests (do not modify)
            - `tests/test_v2_endpoints.py` — v2 regression tests (do not modify)
            - `requirements.txt` — dependencies

            ## Compatibility Matrix

            | Endpoint | v1 Path | v2 Path | Action |
            |----------|---------|---------|--------|
            | E1 ({c['e1_name']}) | `/v1{c['e1_path']}` | `/v2{c['e1_path']}` | ADD shim |
            | E2 ({c['e2_name']}) | `/v1{c['e2_path']}` | `/v2{c['e2_path']}` | ADD shim |
            | E3 ({c['e3_name']}) | `/v1{c['e3_path']}` | `/v2{c['e3_path']}` | ADD shim |
            | E4 ({c['e4_name']}) | _(none)_ | `/v2{c['e4_path']}` | NO shim |
            | E5 ({c['e5_name']}) | `/v1{c['e5_path']}` | `/v2/{c['resource_plural']}/export` | REMOVE shim |

            ## Shim Specifications

            ### E1 — ADD shim: Field Rename at `/v1{c['e1_path']}`

            v2 renames the response field `{c['e1_v1_field']}` -> `{c['e1_v2_field']}`.
            v1 clients still expect `{c['e1_v1_field']}`.

            Add a route at `/v1{c['e1_path']}` that:
            1. Calls the v2 handler logic (or re-uses `v2_{c['e1_name']}`)
            2. In the JSON response, renames `{c['e1_v2_field']}` -> `{c['e1_v1_field']}`

            Example:
            ```python
            @app.route("/v1{c['e1_path']}")
            def v1_{c['e1_name']}(...):
                resp = v2_{c['e1_name']}(...)
                data = resp.get_json()
                data["{c['e1_v1_field']}"] = data.pop("{c['e1_v2_field']}")
                return jsonify(data)
            ```

            ### E2 — ADD shim: Response Restructure at `/v1{c['e2_path']}`

            v2 returns: `{c['e2_v2_shape']}`
            v1 clients expect: `{c['e2_v1_shape']}`

            Add a route at `/v1{c['e2_path']}` that calls v2 and flattens the nested
            response back to the v1 flat shape.

            ### E3 — ADD shim: Default Parameter at `/v1{c['e3_path']}`

            v2 requires query param `{c['e3_v2_param']}`. v1 clients don't send it.

            Add a route at `/v1{c['e3_path']}` that injects
            `{c['e3_v2_param']}={c['e3_v1_default']}` as default when the param is absent,
            then forwards to the v2 handler.

            ### E4 — NO shim: Security Fix at `/v2{c['e4_path']}`

            **Do NOT create `/v1{c['e4_path']}`.**
            {c['e4_security_note']}.
            A v1 shim would silently re-introduce a security vulnerability.
            The correct behavior is to return 404 for the v1 path.

            ### E5 — REMOVE shim: Dead Code at `/v1{c['e5_path']}`

            The route `/v1{c['e5_path']}` currently exists in `app.py` but is dead code.
            {c['e5_stale_reason']}.
            **Delete the `v1_{c['e5_name']}` route function entirely.**

            ## Acceptance Criteria

            1. `GET /v1{c['e1_path']}` (with id=1) returns 200 with `{c['e1_v1_field']}` field (not `{c['e1_v2_field']}`)
            2. `GET /v1{c['e2_path']}` (with id=1) returns 200 with flat v1 shape
            3. `GET /v1{c['e3_path']}` (no params) returns 200 (shim supplies default)
            4. `GET /v1{c['e4_path']}` (with id=1) returns 404 (no shim exists)
            5. `GET /v1{c['e5_path']}` returns 404 (stale shim removed)
            6. All v2 endpoints still return correct responses (regression check)
            7. All tests in `tests/` pass

            ## Authoritative Sources

            - This spec is the authoritative reference for compatibility decisions
            - `compat_matrix.md` in the workspace provides the same information
            - When in doubt: compat_matrix.md > any code comments
            """)

    def _make_brief(self, cfg: dict) -> str:
        c = cfg
        return textwrap.dedent(f"""\
            # API1_version_compat (Brief)

            The {c['service']} Flask API is being upgraded from v1 to v2.
            Add v2 endpoints and ensure v1 backward compatibility is correct.

            **File to modify:** `app.py`
            **Tests:** `python -m pytest tests/ -v` (must pass after changes)
            **Reference:** `compat_matrix.md` documents which endpoints need shims.

            **Do NOT modify:** `compat_matrix.md`, `tests/`, or `requirements.txt`.

            Follow the Planner's guidance precisely.
            """)
