# Reference solution — GH613_celery_10038

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH613_celery_10038`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH613_celery_10038/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CONTRIBUTORS.txt` (modified, +1/-0)
- `celery/app/base.py` (modified, +3/-0)
- `celery/app/task.py` (modified, +3/-0)
- `celery/canvas.py` (modified, +3/-0)
- `celery/local.py` (modified, +3/-0)
- `celery/result.py` (modified, +3/-0)
- `celery/utils/objects.py` (modified, +3/-0)
- `celery/utils/threads.py` (modified, +5/-0)
- `t/unit/test_generics.py` (added, +72/-0)

## `celery/app/base.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `celery/app/task.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `celery/canvas.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `celery/local.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `celery/result.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `celery/app/base.py`
- `celery/app/task.py`
- `celery/canvas.py`
- `celery/local.py`
- `celery/result.py`
