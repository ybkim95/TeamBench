# Reference solution — GH839_psycopg_1217

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH839_psycopg_1217`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH839_psycopg_1217/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news.rst` (modified, +1/-0)
- `psycopg/psycopg/_capabilities.py` (modified, +7/-0)
- `psycopg/psycopg/connection.py` (modified, +1/-1)
- `psycopg/psycopg/connection_async.py` (modified, +1/-1)

## `psycopg/psycopg/_capabilities.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/connection.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/connection_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/_capabilities.py`
- `psycopg/psycopg/connection.py`
- `psycopg/psycopg/connection_async.py`
