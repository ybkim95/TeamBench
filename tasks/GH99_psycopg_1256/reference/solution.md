# Reference solution — GH99_psycopg_1256

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH99_psycopg_1256`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH99_psycopg_1256/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/api/sql.rst` (modified, +6/-16)
- `psycopg/psycopg/_tstrings.py` (modified, +1/-1)
- `psycopg/psycopg/conninfo.py` (modified, +1/-1)

## `psycopg/psycopg/_tstrings.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/conninfo.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/_tstrings.py`
- `psycopg/psycopg/conninfo.py`
