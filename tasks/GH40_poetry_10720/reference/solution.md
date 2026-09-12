# Reference solution — GH40_poetry_10720

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH40_poetry_10720`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH40_poetry_10720/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `src/poetry/packages/locker.py` (modified, +4/-1)
- `tests/installation/fixtures/with-conflicting-dependency-extras-transitive.test` (modified, +4/-4)
- `tests/packages/test_locker.py` (modified, +61/-0)

## `src/poetry/packages/locker.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `src/poetry/packages/locker.py`
