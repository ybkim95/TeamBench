# Reference solution — GH844_psycopg_1177

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH844_psycopg_1177`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH844_psycopg_1177/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/api/cursors.rst` (modified, +6/-0)
- `docs/news.rst` (modified, +4/-4)
- `psycopg/psycopg/cursor.py` (modified, +26/-0)
- `psycopg/psycopg/cursor_async.py` (modified, +26/-0)
- `tests/test_cursor_common.py` (modified, +22/-0)
- `tests/test_cursor_common_async.py` (modified, +22/-0)

## `psycopg/psycopg/cursor.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `psycopg/psycopg/cursor_async.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `psycopg/psycopg/cursor.py`
- `psycopg/psycopg/cursor_async.py`
