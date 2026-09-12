# Reference solution — GH363_celery_10040

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH363_celery_10040`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH363_celery_10040/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `celery/backends/redis.py` (modified, +28/-0)
- `t/unit/backends/test_redis.py` (modified, +92/-0)

## `celery/backends/redis.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `celery/backends/redis.py`
