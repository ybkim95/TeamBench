# CR4: API Design Review Fix

## Goal
Fix all six API design violations identified in the code review of `app.py`.
The API must comply with the API Design Guidelines below after your changes.

All existing tests in `tests/test_api.py` must pass.

---

## Module Under Review

**User Management API** — `app.py`

This module manages user accounts, profiles, and authentication.

---

## API Design Guidelines

### G1 — HTTP Methods
| Intent | Method |
|--------|--------|
| Create resource | **POST** |
| Read resource(s) | **GET** |
| Replace resource | **PUT** |
| Partial update | **PATCH** |
| Delete resource | **DELETE** |

Never use GET for operations that mutate state.
Never use PUT or DELETE for creation.

### G2 — Naming Conventions
- All route path segments must use **snake_case** (e.g. `/search_results`, not `/searchResults`)
- Collection endpoints use plural nouns (e.g. `/users`, not `/user`)
- Python function names must mirror their route in snake_case
- A search/filter endpoint must be named `search_users` and routed to `/search`

### G3 — Pagination
- Every collection `GET` endpoint **must** support pagination via query parameters
- Required parameters: `page` and `page_size`
- Default values: `page=1`, `page_size=20`
- Response envelope must include:
  ```json
  {
    "users": [...paginated slice...],
    "page": <current page>,
    "page_size": <items per page>,
    "total": <total record count>
  }
  ```
- Never return the entire dataset in a single response

### G4 — HTTP Status Codes
| Situation | Code |
|-----------|------|
| Create (POST) success | **201 Created** |
| Read (GET) success | 200 OK |
| Update success | 200 OK |
| Delete success | **204 No Content** |
| Resource not found | **404 Not Found** |
| Invalid client input | **400 Bad Request** |
| Validation failure | 422 Unprocessable Entity |
| Unexpected server error | 500 Internal Server Error |

### G5 — API Versioning
- Every route must be prefixed with `/api/v1/`
- Correct: `GET /api/v1/users`, `POST /api/v1/users`, `DELETE /api/v1/users/<id>`
- Incorrect: `GET /users`, `GET /api/users`, `GET /v1/users`

### G6 — Error Response Schema
Every non-2xx response **must** return JSON conforming to:
```json
{
  "error": "<human-readable description>",
  "code":  "<SCREAMING_SNAKE_CASE identifier>"
}
```
Plain string responses like `return "Not found", 404` are **not permitted**.

---

## Code Review Report — `app.py`

The following six violations were identified. **All must be fixed.**

---

### VIOLATION V1 — Wrong HTTP Method (breaks G1)

**Location**: `create_user()` route decorator

**Problem**: The create endpoint is decorated with `methods=["GET"]`.
Creating a new resource is a mutating operation and **must** use POST.

**Required fix**: Change the route decorator to `methods=["POST"]`.

```python
# Before (WRONG):
@app.route("/users", methods=["GET"])
def create_user():

# After (CORRECT):
@app.route("/api/v1/users", methods=["POST"])
def create_user():
```

---

### VIOLATION V2 — camelCase Route and Function Name (breaks G2)

**Location**: Search/filter endpoint — route `/createPost` and function `createPost`

**Problem**: Both the URL path segment and the Python function name use camelCase
(`createPost`). All routes and functions must use snake_case.

**Required fix**: Rename the route to `/search` and the function to `search_users`.

```python
# Before (WRONG):
@app.route("/users/createPost", methods=["GET"])
def createPost():

# After (CORRECT):
@app.route("/api/v1/users/search", methods=["GET"])
def search_users():
```

---

### VIOLATION V3 — No Pagination on List Endpoint (breaks G3)

**Location**: `list_users()` — `GET /users`

**Problem**: The endpoint returns the entire `_users` store unconditionally.
For any non-trivial dataset this is a reliability and performance hazard.

**Required fix**: Add `page` and `page_size` query parameters and slice the result.

```python
@app.route("/api/v1/users", methods=["GET"])
def list_users():
    page  = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    all_items = list(_users.values())
    start = (page - 1) * page_size
    sliced = all_items[start : start + page_size]
    return jsonify({
        "users":     sliced,
        "page":  page,
        "page_size": page_size,
        "total":   len(all_items),
    })
```

---

### VIOLATION V4 — Wrong HTTP Status Codes (breaks G4)

**Locations and required fixes**:

| Function | Current code | Required code | Reason |
|----------|-------------|---------------|--------|
| `create_user()` success path | `200` | **201** | Resource creation |
| `get_user()` not-found path | `200` | **404** | Resource missing |
| `delete_user()` success path | `200` | **204** | Deletion confirmed |
| `create_user()` + `get_stats()` client-error paths | `500` | **400** | Bad client input |

Update every `return ..., STATUS` to use the correct code from the table above.

---

### VIOLATION V5 — Missing `/api/v1/` Prefix (breaks G5)

**Problem**: All routes currently use prefix `"/users"` instead of `/api/v1/users`.

**Required fix**: Update **every** `@app.route(...)` in the file to use the `/api/v1/` prefix.

```python
# Before:
@app.route("/users", ...)
@app.route("/users/<item_id>", ...)

# After:
@app.route("/api/v1/users", ...)
@app.route("/api/v1/users/<item_id>", ...)
```

This applies to ALL eight routes: list, create, get, update, delete, search, health, stats.

---

### VIOLATION V6 — Bare String Error Responses (breaks G6)

**Problem**: Every non-2xx return in `app.py` uses a bare string:

```python
return "Not found", 404   # WRONG — plain string, not JSON
```

**Required fix**: Replace every error return with `jsonify()` conforming to G6:

```python
return jsonify({"error": "Not found", "code": "NOT_FOUND"}), 404  # CORRECT
```

**Locations** (all must be updated):
- `create_user()` — missing-field validation error (`500`)
- `get_user()` — not-found (`404`)
- `update_user()` — not-found (`404`)
- `delete_user()` — not-found (`404`)
- `get_stats()` — bad `group_by` parameter (`500` → should be `400`)

---

## Summary of All Required Changes

| # | Violation | Location | Fix |
|---|-----------|----------|-----|
| V1 | `GET` used for create | `create_user()` decorator | Change to `POST` |
| V2 | camelCase route `/createPost` | search route + function | Rename to `/search` + `search_users()` |
| V3 | No pagination on list | `list_users()` | Add `page` + `page_size`, slice + envelope |
| V4 | Wrong status codes | create/get/delete/stats | 201 / 404 / 204 / 400 |
| V5 | Missing `/api/v1/` prefix | all 8 routes | Add `/api/v1/` to every route |
| V6 | Bare string errors | 5 error returns | Wrap with `jsonify({"error":..., "code":...})` |

## Deliverables
1. `app.py` with all six violations corrected.
2. `tests/test_api.py` must pass without modification.
3. Verifier writes `attestation.json` with `verdict: pass` once all checks pass.
