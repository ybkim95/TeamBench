"""
Parameterized generator for P3: RBAC Implementation (Role-Based Access Control).

Each seed produces:
  - Different role names (3-5 roles, drawn from a diverse pool)
  - Different endpoint sets (drawn from a pool of REST resource endpoints)
  - Different permission matrix (which roles can GET/POST/PUT/DELETE on which endpoints)
  - Edge-case constraints (e.g. auditor-like role can READ but not WRITE a specific endpoint)
  - A Flask app skeleton with endpoints but no access-control decorators
  - expected.json with the full permission matrix for grading

The task structure is stable: read corpus/rbac_policy.txt, implement decorators
on the Flask app so that allowed requests succeed and denied ones return 403.
"""
from __future__ import annotations

import json
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Role pools ────────────────────────────────────────────────────────────────

ROLE_POOL = [
    # (role_name, description, archetype)
    # archetype: "admin", "editor", "viewer", "auditor", "operator", "owner", "guest"
    ("admin",     "Full system administrator",         "admin"),
    ("superuser", "Elevated privileges administrator", "admin"),
    ("manager",   "Department manager",                "editor"),
    ("editor",    "Content editor",                    "editor"),
    ("operator",  "System operator",                   "operator"),
    ("developer", "Application developer",             "operator"),
    ("analyst",   "Data analyst",                      "viewer"),
    ("viewer",    "Read-only user",                    "viewer"),
    ("reporter",  "Report generator",                  "viewer"),
    ("auditor",   "Compliance auditor",                "auditor"),
    ("monitor",   "System monitor",                    "auditor"),
    ("guest",     "Unauthenticated guest",             "guest"),
    ("readonly",  "Read-only service account",         "viewer"),
    ("support",   "Support staff",                     "editor"),
    ("owner",     "Resource owner",                    "admin"),
]

# ── Endpoint pools ────────────────────────────────────────────────────────────

ENDPOINT_POOL = [
    # (resource, methods_available, description)
    ("users",        ["GET", "POST", "PUT", "DELETE"], "User account management"),
    ("reports",      ["GET", "POST"],                  "Report generation and retrieval"),
    ("settings",     ["GET", "PUT"],                   "System configuration settings"),
    ("audit_log",    ["GET"],                          "Audit trail log (read-only resource)"),
    ("projects",     ["GET", "POST", "PUT", "DELETE"], "Project management"),
    ("documents",    ["GET", "POST", "PUT", "DELETE"], "Document storage and management"),
    ("billing",      ["GET", "POST"],                  "Billing and payment records"),
    ("metrics",      ["GET"],                          "System metrics and monitoring"),
    ("permissions",  ["GET", "PUT"],                   "Permission configuration"),
    ("notifications",["GET", "POST", "DELETE"],        "Notification management"),
    ("exports",      ["GET", "POST"],                  "Data export management"),
    ("webhooks",     ["GET", "POST", "PUT", "DELETE"], "Webhook endpoint management"),
    ("tokens",       ["GET", "POST", "DELETE"],        "API token management"),
    ("groups",       ["GET", "POST", "PUT", "DELETE"], "User group management"),
    ("logs",         ["GET"],                          "Application log access"),
]

# HTTP methods with their CRUD semantic
METHOD_CRUD = {
    "GET":    "read",
    "POST":   "create",
    "PUT":    "update",
    "DELETE": "delete",
}

# ── Archetype permission templates ────────────────────────────────────────────
# For each archetype, defines which CRUD operations are typically allowed
ARCHETYPE_DEFAULTS = {
    "admin":    {"read": True,  "create": True,  "update": True,  "delete": True},
    "editor":   {"read": True,  "create": True,  "update": True,  "delete": False},
    "operator": {"read": True,  "create": True,  "update": True,  "delete": False},
    "viewer":   {"read": True,  "create": False, "update": False, "delete": False},
    "auditor":  {"read": True,  "create": False, "update": False, "delete": False},
    "guest":    {"read": False, "create": False, "update": False, "delete": False},
}

# ── Edge-case constraint templates ────────────────────────────────────────────
# (description_template, constraint_type)
# constraint_type: "read_only_endpoint" — a non-admin role gets read but never write
#                  "no_delete"          — even editors cannot delete this resource
#                  "admin_only"         — only admin archetype can access at all
EDGE_CASE_TEMPLATES = [
    {
        "type": "read_only_endpoint",
        "desc": "The {role} role may only READ {endpoint} — modification is prohibited "
                "regardless of other permissions.",
    },
    {
        "type": "no_delete",
        "desc": "The {endpoint} resource cannot be deleted by any non-admin role. "
                "DELETE on {endpoint} is reserved exclusively for {admin_role}.",
    },
    {
        "type": "admin_only",
        "desc": "Access to {endpoint} is restricted to {admin_role} only. "
                "All other roles receive 403 on any method.",
    },
]


class Generator(TaskGenerator):
    task_id = "P3_access_control"
    domain = "policy"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        # ── Pick roles for this seed (3-5 roles) ──
        num_roles = rng.randint(3, 5)
        role_entries = rng.sample(ROLE_POOL, num_roles)
        # Always ensure at least one admin-archetype role
        has_admin = any(r[2] == "admin" for r in role_entries)
        if not has_admin:
            # Replace last role with an admin role
            admin_options = [r for r in ROLE_POOL if r[2] == "admin"]
            role_entries[-1] = rng.choice(admin_options)

        roles = [(name, desc, arch) for (name, desc, arch) in role_entries]
        admin_role = next(r[0] for r in roles if r[2] == "admin")

        # ── Pick endpoints for this seed (4-6 endpoints) ──
        num_endpoints = rng.randint(4, 6)
        endpoint_entries = rng.sample(ENDPOINT_POOL, num_endpoints)

        # ── Build base permission matrix ──
        # matrix[role_name][endpoint][method] = True/False
        matrix: dict[str, dict[str, dict[str, bool]]] = {}
        for (role_name, _, arch) in roles:
            matrix[role_name] = {}
            defaults = ARCHETYPE_DEFAULTS[arch]
            for (ep_name, ep_methods, _) in endpoint_entries:
                matrix[role_name][ep_name] = {}
                for method in ep_methods:
                    crud = METHOD_CRUD[method]
                    matrix[role_name][ep_name][method] = defaults.get(crud, False)

        # Admin always gets everything
        for (ep_name, ep_methods, _) in endpoint_entries:
            for method in ep_methods:
                matrix[admin_role][ep_name][method] = True

        # ── Apply seed-specific edge cases ──
        edge_cases: list[dict] = []

        # Edge case 1: pick a non-admin "editor/operator" role and restrict it to read-only
        # on one endpoint that has write methods
        writable_eps = [(ep, meths) for (ep, meths, _) in endpoint_entries
                        if any(m in meths for m in ["POST", "PUT", "DELETE"])]
        non_admin_write_roles = [(n, d, a) for (n, d, a) in roles
                                 if a in ("editor", "operator") and n != admin_role]
        if non_admin_write_roles and writable_eps:
            ec_role_name = rng.choice(non_admin_write_roles)[0]
            ec_ep, ec_ep_methods = rng.choice(writable_eps)
            # Make this role read-only on that endpoint
            for method in ec_ep_methods:
                if method != "GET":
                    matrix[ec_role_name][ec_ep][method] = False
            edge_cases.append({
                "type": "read_only_endpoint",
                "role": ec_role_name,
                "endpoint": ec_ep,
                "desc": f"The {ec_role_name} role may only READ {ec_ep} — "
                        f"modification is prohibited regardless of other permissions.",
            })

        # Edge case 2: pick one endpoint where DELETE is restricted to admin only
        delete_eps = [(ep, meths) for (ep, meths, _) in endpoint_entries
                      if "DELETE" in meths]
        if delete_eps:
            no_del_ep, no_del_methods = rng.choice(delete_eps)
            for (role_name, _, arch) in roles:
                if arch != "admin":
                    matrix[role_name][no_del_ep]["DELETE"] = False
            edge_cases.append({
                "type": "no_delete",
                "endpoint": no_del_ep,
                "admin_role": admin_role,
                "desc": f"The {no_del_ep} resource cannot be deleted by any non-admin role. "
                        f"DELETE on {no_del_ep} is reserved exclusively for {admin_role}.",
            })

        # Edge case 3: if there is a "viewer" or "auditor" archetype, it must be read-only globally
        for (role_name, _, arch) in roles:
            if arch in ("viewer", "auditor", "guest"):
                for (ep_name, ep_methods, _) in endpoint_entries:
                    for method in ep_methods:
                        if method != "GET":
                            matrix[role_name][ep_name][method] = False

        # ── Build flat permission list for grading ──
        # permissions: list of {role, endpoint, method, allowed}
        permissions_flat: list[dict] = []
        for (role_name, _, _) in roles:
            for (ep_name, ep_methods, _) in endpoint_entries:
                for method in ep_methods:
                    permissions_flat.append({
                        "role": role_name,
                        "endpoint": ep_name,
                        "method": method,
                        "allowed": matrix[role_name][ep_name][method],
                    })

        # ── Generate corpus/rbac_policy.txt ──
        policy_txt = self._generate_policy(
            roles=roles,
            endpoint_entries=endpoint_entries,
            matrix=matrix,
            edge_cases=edge_cases,
            admin_role=admin_role,
            seed=seed,
        )

        # ── Generate workspace Flask app ──
        app_py = self._generate_flask_app(
            roles=roles,
            endpoint_entries=endpoint_entries,
        )

        # ── Generate workspace rbac.py (stub that agents must implement) ──
        rbac_py = self._generate_rbac_stub(roles=roles)

        # ── expected.json ──
        expected = {
            "roles": [r[0] for r in roles],
            "endpoints": [ep[0] for ep in endpoint_entries],
            "admin_role": admin_role,
            "permissions": permissions_flat,
            "matrix": matrix,
            "edge_cases": edge_cases,
        }

        spec_md = self._generate_spec(
            roles=roles,
            endpoint_entries=endpoint_entries,
            admin_role=admin_role,
            edge_cases=edge_cases,
        )
        brief_md = self._generate_brief()

        corpus_files = {
            "rbac_policy.txt": policy_txt,
        }

        workspace_files = {
            "app.py": app_py,
            "rbac.py": rbac_py,
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files=workspace_files,
            corpus_files=corpus_files,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _generate_policy(
        self,
        roles: list,
        endpoint_entries: list,
        matrix: dict,
        edge_cases: list,
        admin_role: str,
        seed: int,
    ) -> str:
        ver = f"{1 + seed % 4}.{seed % 9}"
        year = 2025 + (seed % 3)

        lines = [
            "ROLE-BASED ACCESS CONTROL POLICY",
            f"Version: {ver}",
            f"Effective Date: {year}-01-01",
            "Classification: INTERNAL",
            "",
            "=== ROLES ===",
            "",
        ]
        for (name, desc, arch) in roles:
            lines.append(f"Role: {name}")
            lines.append(f"  Description: {desc}")
            lines.append(f"  Archetype: {arch}")
            lines.append("")

        lines += [
            "=== ENDPOINTS ===",
            "",
        ]
        for (ep_name, ep_methods, ep_desc) in endpoint_entries:
            methods_str = ", ".join(ep_methods)
            lines.append(f"Endpoint: /{ep_name}")
            lines.append(f"  Description: {ep_desc}")
            lines.append(f"  Available methods: {methods_str}")
            lines.append("")

        lines += [
            "=== PERMISSION MATRIX ===",
            "",
            "Format: ALLOW or DENY for each (role, endpoint, method) combination.",
            "",
        ]

        for (role_name, _, _) in roles:
            lines.append(f"Role: {role_name}")
            for (ep_name, ep_methods, _) in endpoint_entries:
                for method in ep_methods:
                    allowed = matrix[role_name][ep_name][method]
                    verdict = "ALLOW" if allowed else "DENY"
                    lines.append(f"  {method} /{ep_name}: {verdict}")
            lines.append("")

        if edge_cases:
            lines += [
                "=== EDGE CASES AND EXCEPTIONS ===",
                "",
            ]
            for i, ec in enumerate(edge_cases, 1):
                lines.append(f"Exception {i}: {ec['desc']}")
                lines.append("")

        lines += [
            "=== ENFORCEMENT REQUIREMENTS ===",
            "",
            "1. Every endpoint must check the caller's role before processing the request.",
            "2. Requests from roles not listed in the matrix must be rejected with HTTP 403.",
            "3. Requests with no role specified must be rejected with HTTP 403.",
            "4. The permission matrix above is authoritative. Edge cases override the general matrix.",
            f"5. The {admin_role} role has unrestricted access to all endpoints and methods.",
            "6. Access decisions must be logged to audit_trail (list of dicts with role, endpoint, method, allowed).",
            "7. No hardcoded role bypass logic is permitted; all decisions must flow through the",
            "   check_permission() function in rbac.py.",
            "",
            "=== END OF POLICY ===",
        ]

        return "\n".join(lines) + "\n"

    def _generate_flask_app(
        self,
        roles: list,
        endpoint_entries: list,
    ) -> str:
        """Generate a Flask app skeleton with endpoints but no access control."""
        role_names = [r[0] for r in roles]

        lines = [
            '"""',
            "Flask application for RBAC task.",
            "",
            "The endpoints are defined but have NO access control yet.",
            "Implement RBAC by:",
            "  1. Completing rbac.py (check_permission function + PERMISSIONS dict)",
            "  2. Adding @require_role decorators or inline permission checks to each endpoint",
            "",
            "The caller's role is passed via the X-Role request header.",
            '"""',
            "from flask import Flask, request, jsonify, g",
            "from rbac import check_permission, PERMISSIONS",
            "import functools",
            "",
            "app = Flask(__name__)",
            "audit_trail = []  # append {role, endpoint, method, allowed} dicts here",
            "",
            "",
            "def require_permission(endpoint_name):",
            '    """Decorator: enforce RBAC for the given endpoint."""',
            "    def decorator(f):",
            "        @functools.wraps(f)",
            "        def wrapped(*args, **kwargs):",
            "            role = request.headers.get('X-Role', '')",
            "            method = request.method",
            "            allowed = check_permission(role, endpoint_name, method)",
            "            audit_trail.append({",
            "                'role': role,",
            "                'endpoint': endpoint_name,",
            "                'method': method,",
            "                'allowed': allowed,",
            "            })",
            "            if not allowed:",
            "                return jsonify({'error': 'Forbidden'}), 403",
            "            return f(*args, **kwargs)",
            "        return wrapped",
            "    return decorator",
            "",
            "",
        ]

        # Generate each endpoint — NO access control applied yet (agent must add it)
        for (ep_name, ep_methods, ep_desc) in endpoint_entries:
            methods_str = ", ".join(f'"{m}"' for m in ep_methods)
            # Route definition
            lines.append(f"@app.route('/{ep_name}', methods=[{methods_str}])")
            lines.append(f"def {ep_name}_handler():")
            lines.append(f'    """Handle {ep_desc}. TODO: add RBAC enforcement."""')
            lines.append("    # TODO: enforce RBAC here using require_permission or check_permission")
            lines.append(f"    return jsonify({{'resource': '{ep_name}', 'method': request.method}}), 200")
            lines.append("")
            lines.append("")

        lines += [
            "@app.route('/audit', methods=['GET'])",
            "def audit_handler():",
            '    """Return audit trail — no RBAC on this endpoint."""',
            "    return jsonify({'audit_trail': audit_trail}), 200",
            "",
            "",
            "if __name__ == '__main__':",
            "    app.run(debug=False)",
        ]

        return "\n".join(lines) + "\n"

    def _generate_rbac_stub(self, roles: list) -> str:
        """Generate rbac.py stub that the agent must fill in."""
        role_names = [r[0] for r in roles]
        roles_comment = ", ".join(f'"{n}"' for n in role_names)

        lines = [
            '"""',
            "RBAC module — implement the permission table and check function.",
            "",
            "PERMISSIONS dict structure:",
            "  {",
            "    role_name: {",
            "      endpoint_name: [list_of_allowed_methods],",
            "      ...",
            "    },",
            "    ...",
            "  }",
            "",
            "Read corpus/rbac_policy.txt for the authoritative permission matrix.",
            '"""',
            "",
            f"# Roles in this deployment: {roles_comment}",
            "# TODO: populate PERMISSIONS from corpus/rbac_policy.txt",
            "PERMISSIONS: dict[str, dict[str, list[str]]] = {",
            "    # role_name: {endpoint: [allowed_methods]}",
            "}",
            "",
            "",
            "def check_permission(role: str, endpoint: str, method: str) -> bool:",
            '    """',
            "    Return True if the given role may perform method on endpoint.",
            "    Return False for unknown roles, unknown endpoints, or denied methods.",
            '    """',
            "    # TODO: implement using PERMISSIONS dict",
            "    return False  # placeholder — replace with real logic",
        ]

        return "\n".join(lines) + "\n"

    def _generate_spec(
        self,
        roles: list,
        endpoint_entries: list,
        admin_role: str,
        edge_cases: list,
    ) -> str:
        role_list = "\n".join(
            f"- **{name}** ({arch}): {desc}" for (name, desc, arch) in roles
        )
        ep_list = "\n".join(
            f"- `/{ep}` ({', '.join(methods)}): {desc}"
            for (ep, methods, desc) in endpoint_entries
        )
        edge_list = "\n".join(
            f"- {ec['desc']}" for ec in edge_cases
        ) if edge_cases else "None"

        return f"""# P3: RBAC Implementation

## Goal
Implement role-based access control (RBAC) for the Flask web application so that each
endpoint enforces the permission matrix defined in `corpus/rbac_policy.txt`.

## Context

**Roles in this deployment:**
{role_list}

**Endpoints:**
{ep_list}

**Edge cases / exceptions:**
{edge_list}

The `{admin_role}` role has unrestricted access to all endpoints.

## Hard Requirements

1. Implement `PERMISSIONS` dict in `rbac.py` containing the complete permission matrix
   from `corpus/rbac_policy.txt`.
2. Implement `check_permission(role, endpoint, method)` in `rbac.py` to return `True`
   if the role is allowed, `False` otherwise (unknown role/endpoint/method → `False`).
3. Apply access control to every endpoint in `app.py`:
   - Use the `require_permission` decorator OR call `check_permission` inline.
   - Denied requests must return HTTP 403 with JSON `{{"error": "Forbidden"}}`.
   - Allowed requests must return HTTP 200 with the resource response.
4. Log every access decision to `audit_trail` (already defined in `app.py`).
5. The caller's role is passed via the `X-Role` HTTP request header.
6. No hardcoded bypasses — all decisions must flow through `check_permission()`.
7. Edge cases in the policy document override the general permission matrix.

## Policy Source

Read `corpus/rbac_policy.txt` to obtain the authoritative role-permission matrix and
all edge cases. The Planner must derive the `PERMISSIONS` dict directly from that document.

## Deliverables
- `rbac.py` with `PERMISSIONS` dict populated and `check_permission()` implemented.
- `app.py` with `require_permission` decorator applied to every endpoint.
- Verifier must test each (role, endpoint, method) combination from the matrix and
  confirm that allowed combinations return 200 and denied combinations return 403,
  then produce `output/attestation.json` with verdict.
"""

    def _generate_brief(self) -> str:
        return """# P3: RBAC Implementation (Brief)

Implement role-based access control for the Flask app.
The Planner has the full role-permission matrix from `corpus/rbac_policy.txt`.

Tasks:
1. Fill in `PERMISSIONS` dict in `rbac.py` (from policy doc).
2. Implement `check_permission()` in `rbac.py`.
3. Apply `require_permission` decorator to every endpoint in `app.py`.
4. Denied requests must return 403; allowed must return 200.
"""
