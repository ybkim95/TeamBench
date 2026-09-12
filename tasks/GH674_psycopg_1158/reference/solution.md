# Reference solution — GH674_psycopg_1158

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH674_psycopg_1158`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH674_psycopg_1158/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/news.rst` (modified, +2/-0)
- `psycopg/psycopg/_py_transformer.py` (modified, +4/-0)
- `psycopg_c/psycopg_c/_psycopg/copy.pyx` (modified, +31/-3)
- `psycopg_c/psycopg_c/_psycopg/transform.pyx` (modified, +2/-0)
- `psycopg_c/psycopg_c/types/numeric.pyx` (modified, +17/-4)
- `tests/test_copy.py` (modified, +31/-0)
- `tests/test_copy_async.py` (modified, +31/-0)

## `psycopg/psycopg/_py_transformer.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `psycopg/psycopg/_py_transformer.py`
