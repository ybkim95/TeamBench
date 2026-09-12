# Reference solution — GH855_psycopg_1227

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH855_psycopg_1227`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH855_psycopg_1227/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news.rst` (modified, +9/-0)
- `psycopg/psycopg/_server_cursor.py` (modified, +1/-1)
- `psycopg/psycopg/_server_cursor_async.py` (modified, +1/-1)
- `psycopg/pyproject.toml` (modified, +3/-3)
- `psycopg_c/pyproject.toml` (modified, +1/-1)
- `psycopg_pool/pyproject.toml` (modified, +1/-1)
- `tests/test_cursor_server.py` (modified, +1/-1)
- `tests/test_cursor_server_async.py` (modified, +1/-1)

## `psycopg/psycopg/_server_cursor.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/_server_cursor_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/_server_cursor.py`
- `psycopg/psycopg/_server_cursor_async.py`
