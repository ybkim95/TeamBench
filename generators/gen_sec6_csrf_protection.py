"""
Parameterized generator for SEC6: CSRF Protection.

Each seed produces:
- A different Flask app domain (profile management, settings, admin panel,
  e-commerce checkout, comment system)
- Different endpoint names, form field names, and cookie names
- Different token strategy label (per-session double-submit cookie always, but
  cookie/header names vary)
- Same TNI Pattern C structure: spec lists which endpoints need protection and
  which are exempt, brief says "add CSRF protection"

TNI Design:
  - brief.md: vague — "The web app lacks CSRF protection. Add it."
  - spec.md: precise — lists every protected endpoint (POST/PUT/DELETE state-
    changers), every exempt endpoint (public read-only, HMAC-signed webhook),
    the token strategy (per-session, double-submit cookie), and the exact error
    response for CSRF failures (HTTP 403 JSON body).
  - workspace: Flask app with multiple forms/endpoints, no CSRF tokens present.

Grade checks (10+):
  1. CSRF token generated and stored in session on GET of protected form pages
  2. CSRF token embedded in HTML forms on protected pages
  3. Protected POST/PUT/DELETE endpoints reject requests without valid token (403)
  4. Protected endpoints accept requests with valid token
  5. Exempt read-only endpoints work without any token (no false positives)
  6. Exempt webhook endpoint works with HMAC signature without CSRF token
  7. Error response on CSRF failure is HTTP 403 with correct JSON body
  8. Token is per-session (different sessions → different tokens)
  9. Double-submit cookie set on form pages
  10. Syntax valid, no broken routes
  11. No new vulnerabilities introduced (no eval/exec)
  12. Attestation check
"""
from __future__ import annotations

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Variation pools ──────────────────────────────────────────────────────────

APP_DOMAINS = [
    {
        "name": "profile_manager",
        "label": "Profile Manager",
        "resource": "profile",
        # Protected state-changing endpoints
        "protected": [
            {"path": "/profile/update",   "method": "POST", "func": "update_profile",   "form_page": "/profile/edit"},
            {"path": "/profile/password", "method": "POST", "func": "change_password",  "form_page": "/profile/security"},
            {"path": "/profile/delete",   "method": "POST", "func": "delete_account",   "form_page": "/profile/danger"},
        ],
        # Exempt endpoints (read-only or HMAC-signed)
        "exempt": [
            {"path": "/profile/view",    "method": "GET",  "func": "view_profile",   "reason": "read-only"},
            {"path": "/profile/search",  "method": "GET",  "func": "search_profiles","reason": "read-only"},
            {"path": "/webhook/profile", "method": "POST", "func": "webhook_profile", "reason": "hmac_signed"},
        ],
        "fields": {"name": "display_name", "bio": "user_bio", "email": "contact_email"},
        "cookie_name": "csrf_token",
        "header_name": "X-CSRF-Token",
        "webhook_secret_var": "WEBHOOK_SECRET",
    },
    {
        "name": "settings_panel",
        "label": "Settings Panel",
        "resource": "settings",
        "protected": [
            {"path": "/settings/save",         "method": "POST", "func": "save_settings",       "form_page": "/settings"},
            {"path": "/settings/notifications", "method": "PUT",  "func": "update_notifications","form_page": "/settings/notify"},
            {"path": "/settings/reset",         "method": "POST", "func": "reset_settings",      "form_page": "/settings/danger"},
        ],
        "exempt": [
            {"path": "/settings/view",  "method": "GET",  "func": "view_settings",   "reason": "read-only"},
            {"path": "/api/config",     "method": "GET",  "func": "get_config",      "reason": "read-only"},
            {"path": "/webhook/config", "method": "POST", "func": "webhook_config",  "reason": "hmac_signed"},
        ],
        "fields": {"theme": "ui_theme", "lang": "language_code", "tz": "timezone"},
        "cookie_name": "csrf_tok",
        "header_name": "X-CSRF-Token",
        "webhook_secret_var": "CONFIG_WEBHOOK_SECRET",
    },
    {
        "name": "admin_console",
        "label": "Admin Console",
        "resource": "admin",
        "protected": [
            {"path": "/admin/user/ban",    "method": "POST",   "func": "ban_user",      "form_page": "/admin/users"},
            {"path": "/admin/user/update", "method": "PUT",    "func": "update_user",   "form_page": "/admin/users/edit"},
            {"path": "/admin/post/remove", "method": "DELETE", "func": "remove_post",   "form_page": "/admin/posts"},
        ],
        "exempt": [
            {"path": "/admin/dashboard", "method": "GET",  "func": "dashboard",       "reason": "read-only"},
            {"path": "/admin/logs",      "method": "GET",  "func": "view_logs",       "reason": "read-only"},
            {"path": "/webhook/admin",   "method": "POST", "func": "webhook_admin",   "reason": "hmac_signed"},
        ],
        "fields": {"user_id": "target_user_id", "reason": "ban_reason", "duration": "ban_days"},
        "cookie_name": "admin_csrf",
        "header_name": "X-Admin-CSRF",
        "webhook_secret_var": "ADMIN_WEBHOOK_SECRET",
    },
    {
        "name": "checkout_flow",
        "label": "Checkout Flow",
        "resource": "order",
        "protected": [
            {"path": "/cart/add",      "method": "POST", "func": "add_to_cart",     "form_page": "/shop/catalog"},
            {"path": "/cart/remove",   "method": "POST", "func": "remove_from_cart","form_page": "/shop/cart"},
            {"path": "/order/place",   "method": "POST", "func": "place_order",     "form_page": "/shop/checkout"},
        ],
        "exempt": [
            {"path": "/catalog",         "method": "GET",  "func": "view_catalog",   "reason": "read-only"},
            {"path": "/cart/view",       "method": "GET",  "func": "view_cart",      "reason": "read-only"},
            {"path": "/webhook/payment", "method": "POST", "func": "webhook_payment","reason": "hmac_signed"},
        ],
        "fields": {"item": "product_id", "qty": "quantity", "addr": "shipping_address"},
        "cookie_name": "shop_csrf",
        "header_name": "X-Shop-CSRF",
        "webhook_secret_var": "PAYMENT_WEBHOOK_SECRET",
    },
    {
        "name": "comment_system",
        "label": "Comment System",
        "resource": "comment",
        "protected": [
            {"path": "/comments/post",   "method": "POST",   "func": "post_comment",   "form_page": "/article"},
            {"path": "/comments/edit",   "method": "PUT",    "func": "edit_comment",   "form_page": "/comments/editor"},
            {"path": "/comments/delete", "method": "DELETE", "func": "delete_comment", "form_page": "/comments/manage"},
        ],
        "exempt": [
            {"path": "/comments/list",    "method": "GET",  "func": "list_comments",  "reason": "read-only"},
            {"path": "/api/articles",     "method": "GET",  "func": "get_articles",   "reason": "read-only"},
            {"path": "/webhook/comments", "method": "POST", "func": "webhook_comments","reason": "hmac_signed"},
        ],
        "fields": {"body": "comment_body", "article": "article_id", "parent": "parent_id"},
        "cookie_name": "comment_csrf",
        "header_name": "X-Comment-CSRF",
        "webhook_secret_var": "COMMENTS_WEBHOOK_SECRET",
    },
]

SECRET_KEY_NAMES = [
    "FLASK_SECRET_KEY",
    "APP_SECRET",
    "SESSION_SECRET",
    "WEB_SECRET_KEY",
    "SITE_SECRET",
]

CSRF_ERROR_MESSAGES = [
    "CSRF token missing or invalid",
    "Invalid or missing CSRF token",
    "CSRF validation failed",
    "Request blocked: CSRF token mismatch",
    "Forbidden: CSRF check failed",
]


class Generator(TaskGenerator):
    task_id = "SEC6_csrf_protection"
    domain = "security"
    difficulty = "medium"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        domain = APP_DOMAINS[rng.randint(0, len(APP_DOMAINS) - 1)]
        secret_key_name = SECRET_KEY_NAMES[rng.randint(0, len(SECRET_KEY_NAMES) - 1)]
        csrf_error_msg = CSRF_ERROR_MESSAGES[rng.randint(0, len(CSRF_ERROR_MESSAGES) - 1)]

        expected = {
            "app_domain": domain["name"],
            "cookie_name": domain["cookie_name"],
            "header_name": domain["header_name"],
            "token_strategy": "per-session double-submit cookie",
            "protected_endpoints": [ep["path"] for ep in domain["protected"]],
            "exempt_endpoints": [ep["path"] for ep in domain["exempt"]],
            "csrf_error_status": 403,
            "csrf_error_body_key": "error",
            "csrf_error_msg": csrf_error_msg,
            "secret_key_name": secret_key_name,
            "webhook_secret_var": domain["webhook_secret_var"],
        }

        workspace_files = {
            "app.py":           self._gen_app(domain, secret_key_name, csrf_error_msg),
            "requirements.txt": self._gen_requirements(),
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=self._gen_spec(domain, csrf_error_msg),
            brief_md=self._gen_brief(domain),
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── workspace file generators ─────────────────────────────────────────────

    def _gen_app(self, domain: dict, secret_key_name: str, csrf_error_msg: str) -> str:
        resource = domain["resource"]
        cookie_name = domain["cookie_name"]
        webhook_secret_var = domain["webhook_secret_var"]

        # Build route functions for protected endpoints (no CSRF protection yet)
        protected_routes = ""
        for ep in domain["protected"]:
            method_list = f'["{ep["method"]}"]'
            func = ep["func"]
            path = ep["path"]
            protected_routes += f"""

@app.route("{path}", methods={method_list})
def {func}():
    \"\"\"State-changing endpoint — must be CSRF-protected.\"\"\"
    data = request.get_json(force=True) or request.form.to_dict()
    # TODO: Validate CSRF token before processing
    return jsonify({{"status": "ok", "action": "{func}", "data": data}})
"""

        # Build route functions for read-only exempt endpoints
        exempt_routes = ""
        for ep in domain["exempt"]:
            if ep["reason"] == "read-only":
                func = ep["func"]
                path = ep["path"]
                exempt_routes += f"""

@app.route("{path}", methods=["GET"])
def {func}():
    \"\"\"Read-only endpoint — CSRF protection not required.\"\"\"
    return jsonify({{"status": "ok", "endpoint": "{path}", "data": []}})
"""
            else:
                # HMAC webhook
                func = ep["func"]
                path = ep["path"]
                exempt_routes += f"""

@app.route("{path}", methods=["POST"])
def {func}():
    \"\"\"Webhook endpoint authenticated via HMAC-SHA256 signature.
    CSRF protection not required — uses HMAC instead.
    \"\"\"
    import hmac as _hmac, hashlib as _hashlib, os as _os
    secret = _os.environ.get("{webhook_secret_var}", "dev-webhook-secret").encode()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    body = request.get_data()
    expected_sig = "sha256=" + _hmac.new(secret, body, _hashlib.sha256).hexdigest()
    if not _hmac.compare_digest(sig_header, expected_sig):
        return jsonify({{"error": "invalid signature"}}), 401
    payload = request.get_json(force=True) or {{}}
    return jsonify({{"status": "received", "payload": payload}})
"""

        # Build a simple form page (GET) for one of the protected endpoints
        form_pages = ""
        for ep in domain["protected"]:
            form_path = ep["form_page"]
            form_func = ep["func"] + "_form"
            action_path = ep["path"]
            form_pages += f"""

@app.route("{form_path}", methods=["GET"])
def {form_func}():
    \"\"\"Renders an HTML form that POSTs to {action_path}.
    TODO: Embed CSRF token in the form and set the double-submit cookie.
    \"\"\"
    html = \"\"\"<!DOCTYPE html>
<html><head><title>{domain["label"]}</title></head><body>
<form method="POST" action="{action_path}">
  <!-- TODO: add <input type="hidden" name="csrf_token" value="..."> -->
  <button type="submit">Submit</button>
</form>
</body></html>\"\"\"
    return html
"""

        return f'''\
"""
{domain["label"]} — Flask web application.

SECURITY NOTE: This application currently lacks CSRF protection.
State-changing endpoints (POST/PUT/DELETE) must validate CSRF tokens before
processing requests. See the task spec for the full list of endpoints that
require protection and which are exempt.
"""
from __future__ import annotations

import os
import secrets

from flask import Flask, jsonify, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("{secret_key_name}", "dev-secret-change-me")


# ── Helper (stub) ─────────────────────────────────────────────────────────────

def _check_csrf():
    """Placeholder — CSRF validation not yet implemented.

    This function should:
    1. Read the CSRF token from request.form["csrf_token"] or the
       "{domain["header_name"]}" header.
    2. Compare it against the token stored in session["{cookie_name}"].
    3. Return True if they match, False otherwise.
    """
    return True  # BUG: always returns True — no actual validation


# ── Protected endpoints (require CSRF token) ──────────────────────────────────
{protected_routes}

# ── Form pages (render HTML with forms) ──────────────────────────────────────
{form_pages}

# ── Exempt endpoints (no CSRF required) ──────────────────────────────────────
{exempt_routes}

# ── Application entry point ───────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False)
'''

    def _gen_requirements(self) -> str:
        return """\
Flask>=2.3.0
"""

    # ── doc generators ─────────────────────────────────────────────────────────

    def _gen_spec(self, domain: dict, csrf_error_msg: str) -> str:
        cookie_name = domain["cookie_name"]
        header_name = domain["header_name"]
        webhook_secret_var = domain["webhook_secret_var"]

        protected_table_rows = "\n".join(
            f"| `{ep['path']}` | `{ep['method']}` | Yes — state-changing |"
            for ep in domain["protected"]
        )
        exempt_table_rows = "\n".join(
            f"| `{ep['path']}` | `{ep['method']}` | No — {ep['reason'].replace('_', ' ')} |"
            for ep in domain["exempt"]
        )

        form_page_list = "\n".join(
            f"- `{ep['form_page']}` (GET) → submits to `{ep['path']}`"
            for ep in domain["protected"]
        )

        return f"""\
# SEC6: CSRF Protection — Full Specification (Planner/Verifier)

## Overview

The **{domain["label"]}** Flask application processes state-changing HTTP
requests without verifying that they originate from the legitimate site.
Cross-Site Request Forgery (CSRF) attacks exploit this by tricking an
authenticated user's browser into making unauthorized requests.

This specification defines exactly which endpoints require CSRF protection,
which are exempt, the token implementation strategy, and the required error
response format.

---

## 1. Endpoint Classification

### 1.1 Protected Endpoints (CSRF token REQUIRED)

All state-changing requests (POST, PUT, DELETE) that operate on user data
must validate a CSRF token before processing:

| Endpoint | Method | Reason |
|----------|--------|--------|
{protected_table_rows}

### 1.2 Exempt Endpoints (CSRF token NOT required)

The following endpoints must work without a CSRF token. Do NOT add CSRF
checks to these — doing so breaks legitimate clients:

| Endpoint | Method | Reason |
|----------|--------|--------|
{exempt_table_rows}

**Exemption rationale**:
- Read-only endpoints (`GET`) do not mutate state and cannot be CSRF vectors.
- The webhook endpoint is authenticated via HMAC-SHA256 (`{webhook_secret_var}`
  environment variable) and is called by external services that cannot carry
  session cookies. Adding CSRF to it would break all webhook deliveries.

---

## 2. Token Implementation Strategy

**Strategy**: Per-session double-submit cookie.

### 2.1 Token Generation

- On every GET request to a form page, generate a cryptographically random
  token using `secrets.token_hex(32)` (or equivalent 32-byte source).
- Store the token in the server-side session: `session["{cookie_name}"] = token`.
- Also set a cookie named `{cookie_name}` with the same token value so the
  browser can read it for JavaScript-driven double-submit flows.
- Embed the token in every HTML form as a hidden input:
  `<input type="hidden" name="csrf_token" value="<token>">`.

### 2.2 Token Validation

On every protected POST/PUT/DELETE request:
1. Read the submitted token from `request.form.get("csrf_token")` or the
   `{header_name}` request header (either is acceptable).
2. Read the expected token from `session.get("{cookie_name}")`.
3. Compare with `secrets.compare_digest(submitted, expected)` to prevent
   timing attacks.
4. If either value is missing or they do not match → return an error response
   (see §3).

### 2.3 Token Lifecycle

- Tokens are per-session: a new session gets a new token.
- Tokens MAY be regenerated per request for extra security, but at minimum
  must persist for the duration of the session.
- Tokens must NOT be URL parameters (they would appear in logs/referrers).

---

## 3. Error Response for CSRF Failures

When a protected endpoint receives a request with a missing or invalid CSRF
token, it MUST respond with:

- **HTTP status**: `403`
- **Content-Type**: `application/json`
- **Body**:
```json
{{"error": "{csrf_error_msg}"}}
```

No redirect, no HTML page — exactly the JSON body above with status 403.

---

## 4. Form Pages

The following GET endpoints render HTML forms. Each must:
1. Generate (or reuse) the session CSRF token.
2. Set the `{cookie_name}` cookie in the response.
3. Include `<input type="hidden" name="csrf_token" value="<token>">` in
   every `<form>` that submits to a protected endpoint.

Form pages:
{form_page_list}

---

## 5. Fix Requirements Summary

| # | Requirement | Location |
|---|-------------|----------|
| 1 | Generate CSRF token and store in session on form page GET | `app.py` form routes |
| 2 | Embed token as hidden input in all protected forms | `app.py` form routes |
| 3 | Set `{cookie_name}` cookie with token value | `app.py` form routes |
| 4 | Validate token on all protected POST/PUT/DELETE endpoints | `app.py` protected routes |
| 5 | Return HTTP 403 JSON on CSRF failure | `app.py` `_check_csrf()` or inline |
| 6 | Leave exempt endpoints (read-only + webhook) untouched | `app.py` exempt routes |
| 7 | Use `secrets.compare_digest` for constant-time comparison | `app.py` |

## 6. Deliverables

The Executor must modify `app.py` to implement the above. The Verifier must
confirm:
- All protected endpoints reject requests without a valid CSRF token (HTTP 403).
- All protected endpoints accept requests with a valid CSRF token (HTTP 200).
- All exempt endpoints respond normally without any CSRF token.
- The webhook endpoint works with an HMAC signature and no CSRF token.
- Form pages set the session token and cookie and embed it in HTML.
"""

    def _gen_brief(self, domain: dict) -> str:
        return f"""\
# SEC6: CSRF Protection (Executor Brief)

The **{domain["label"]}** web application lacks CSRF protection.

Add CSRF protection to the application. The Planner has the full specification
detailing which endpoints need protection and which are exempt.

**Your workspace contains**:
- `app.py` — Flask application with all routes (no CSRF protection yet)
- `requirements.txt` — Python dependencies

Do not change the public API surface (URL paths, HTTP methods, response shapes
for successful requests).
"""
