# Reference solution — GH485_bootrun-backend_111

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH485_bootrun-backend_111`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH485_bootrun-backend_111/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py` (added, +39/-0)
- `app/models/progress.py` (modified, +2/-1)
- `app/services/enrollment_service.py` (modified, +36/-9)

## `alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `app/models/progress.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `app/services/enrollment_service.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `alembic/versions/a3a28d52a24f_add_unique_watched_seconds_to_progress.py`
- `app/models/progress.py`
- `app/services/enrollment_service.py`
