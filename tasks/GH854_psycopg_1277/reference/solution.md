# Reference solution — GH854_psycopg_1277

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH854_psycopg_1277`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH854_psycopg_1277/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news_pool.rst` (modified, +10/-0)
- `psycopg_pool/psycopg_pool/pool.py` (modified, +6/-4)
- `psycopg_pool/psycopg_pool/pool_async.py` (modified, +6/-4)
- `tests/pool/test_pool_async.py` (modified, +63/-0)

## `psycopg_pool/psycopg_pool/pool.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg_pool/psycopg_pool/pool_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg_pool/psycopg_pool/pool.py`
- `psycopg_pool/psycopg_pool/pool_async.py`
