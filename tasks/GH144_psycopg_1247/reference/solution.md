# Reference solution — GH144_psycopg_1247

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH144_psycopg_1247`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH144_psycopg_1247/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news.rst` (modified, +7/-0)
- `psycopg/psycopg/connection.py` (modified, +2/-1)
- `psycopg/psycopg/connection_async.py` (modified, +2/-1)
- `tests/test_connection.py` (modified, +21/-1)
- `tests/test_connection_async.py` (modified, +21/-1)

## `psycopg/psycopg/connection.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/connection_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/connection.py`
- `psycopg/psycopg/connection_async.py`
