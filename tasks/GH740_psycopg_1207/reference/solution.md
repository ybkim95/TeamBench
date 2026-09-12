# Reference solution — GH740_psycopg_1207

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH740_psycopg_1207`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH740_psycopg_1207/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news.rst` (modified, +2/-0)
- `psycopg/psycopg/_conninfo_attempts.py` (modified, +5/-3)
- `psycopg/psycopg/_conninfo_attempts_async.py` (modified, +5/-3)
- `tests/test_connection.py` (modified, +8/-0)
- `tests/test_connection_async.py` (modified, +8/-0)

## `psycopg/psycopg/_conninfo_attempts.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/_conninfo_attempts_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/_conninfo_attempts.py`
- `psycopg/psycopg/_conninfo_attempts_async.py`
