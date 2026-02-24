# JS1 — API Migration (Planner Specification)

> **Planner eyes only.** This document contains the full list of breaking changes that must be communicated to the executor. The executor only has access to `brief.md` and the workspace files.

---

## Overview

The workspace contains an Express v4 application that uses four patterns that were **removed or renamed in Express v5**. The planner must identify all four issues and clearly communicate them to the executor, who will make the code changes.

---

## Breaking Changes That Must Be Fixed

### 1. `req.param()` removed

Express v4 provided the convenience method `req.param(name)` which looked up a value in `req.params`, `req.body`, and `req.query` in order. Express v5 removed this method entirely.

**v4 (broken in v5):**
```js
const id = req.param('id');
```

**v5 fix — use the specific source:**
```js
const id = req.params.id;   // for route parameters
// or req.query.id           // for query-string parameters
// or req.body.id            // for body parameters
```

In `server.js` the call appears in route handlers that have `:id` in their path, so `req.params.id` is the correct replacement.

---

### 2. `res.json()` second-argument status removed

Express v4 accepted an optional second argument to `res.json()` as the HTTP status code:

```js
res.json(data, 200);   // v4 — second arg is status
```

Express v5 removed this overload. The status must be set via `res.status()` chained before `.json()`:

```js
res.status(200).json(data);   // v5
```

Search `server.js` for any call matching `res.json(` with two arguments and rewrite them.

---

### 3. `app.del()` renamed to `app.delete()`

Express v4 provided `app.del()` as an alias for `app.delete()` because `delete` is a reserved word in older JavaScript environments. Express v5 dropped the alias; only `app.delete()` is valid.

**v4 (broken in v5):**
```js
app.del('/tasks/:id', handler);
```

**v5 fix:**
```js
app.delete('/tasks/:id', handler);
```

---

### 4. Regex route parameter syntax changed

Express v4 allowed inline regex constraints in route paths:

```js
app.get('/user/:id(\\d+)', handler);   // v4
```

Express v5 no longer supports the inline `(regex)` syntax after a parameter name. Use a plain parameter and validate manually, or use the new named-parameter syntax with `{name}`. The simplest migration is to drop the constraint:

```js
app.get('/user/:id', handler);   // v5 — validate inside handler if needed
```

---

### 5. Error handler must set status explicitly

Express v4 allowed error handlers to omit `res.status()` and the framework might fall back to a default. Express v5 requires the error handler to set the status code explicitly before sending. The signature itself (`(err, req, res, next)`) is unchanged, but the handler body must call `res.status(n)`.

**Fix pattern:**
```js
app.use((err, req, res, next) => {
  res.status(err.status || 500).json({ error: err.message });
});
```

---

### 6. `package.json` dependency must be updated

The current `package.json` pins `"express": "^4.18.2"`. Change it to `"express": "^5.0.0"` so that `npm install` (or equivalent) fetches Express v5.

---

## File Map

| File | What needs to change |
|---|---|
| `package.json` | `express` version `^4.18.2` → `^5.0.0` |
| `server.js` | Fix all five patterns above |
| `test/api.test.js` | **Do not modify** — tests are written against observable HTTP behaviour and pass with both v4-correct and v5-correct code |

---

## Test Suite Reference

`test/api.test.js` runs five tests via the built-in `http` module:

| # | Test | Expected |
|---|---|---|
| 1 | `GET /tasks` | 200, JSON array |
| 2 | `POST /tasks` | 201, JSON task object |
| 3 | `GET /tasks/:id` | 200, same task |
| 4 | `PUT /tasks/:id` | 200, updated task |
| 5 | `DELETE /tasks/:id` | 204, empty body |

All five tests must exit the suite with code `0`.

---

## Communication Checklist for Planner → Executor

When writing instructions to the executor, cover:

- [ ] Which npm version of express to pin in `package.json`
- [ ] Replace every `req.param('id')` with `req.params.id`
- [ ] Rewrite every `res.json(data, status)` to `res.status(status).json(data)`
- [ ] Rename `app.del(` to `app.delete(`
- [ ] Remove inline regex from route path `/user/:id(\\d+)` → `/user/:id`
- [ ] Ensure error handler calls `res.status(...)` before `.json(...)`
- [ ] Create `attestation.json` with `{"verdict": "pass"}` once all tests pass
