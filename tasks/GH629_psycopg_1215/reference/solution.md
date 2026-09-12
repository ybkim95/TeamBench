# Reference solution — GH629_psycopg_1215

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH629_psycopg_1215`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH629_psycopg_1215/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/api/pool.rst` (modified, +4/-0)
- `docs/news_pool.rst` (modified, +5/-4)
- `psycopg/psycopg/_connection_base.py` (modified, +2/-0)
- `psycopg_pool/psycopg_pool/base.py` (modified, +3/-1)
- `psycopg_pool/psycopg_pool/pool.py` (modified, +21/-1)
- `psycopg_pool/psycopg_pool/pool_async.py` (modified, +21/-1)
- `tests/pool/test_pool_common.py` (modified, +34/-0)
- `tests/pool/test_pool_common_async.py` (modified, +34/-0)

## `psycopg/psycopg/_connection_base.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg_pool/psycopg_pool/base.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg_pool/psycopg_pool/pool.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg_pool/psycopg_pool/pool_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/_connection_base.py`
- `psycopg_pool/psycopg_pool/base.py`
- `psycopg_pool/psycopg_pool/pool.py`
- `psycopg_pool/psycopg_pool/pool_async.py`
