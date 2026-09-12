# Reference solution — GH158_attrs_1529

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH158_attrs_1529`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH158_attrs_1529/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `changelog.d/1529.change.md` (added, +1/-0)
- `docs/api.rst` (modified, +2/-0)
- `src/attr/__init__.pyi` (modified, +1/-1)
- `src/attr/_make.py` (modified, +10/-5)
- `tests/test_make.py` (modified, +11/-4)
- `tests/test_mypy.yml` (modified, +12/-1)

## `src/attr/_make.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `src/attr/_make.py`
