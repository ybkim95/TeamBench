# Reference solution — GH707_psycopg_1150

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH707_psycopg_1150`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH707_psycopg_1150/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `psycopg/psycopg/_copy_base.py` (modified, +4/-17)
- `psycopg_c/psycopg_c/_psycopg.pyi` (modified, +4/-4)
- `psycopg_c/psycopg_c/_psycopg/copy.pyx` (modified, +44/-33)
- `tests/test_copy.py` (modified, +15/-0)
- `tests/test_copy_async.py` (modified, +17/-0)

## `psycopg/psycopg/_copy_base.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `psycopg/psycopg/_copy_base.py`
