# Reference solution — GH499_TileOPs_570

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH499_TileOPs_570`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH499_TileOPs_570/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `.foundry/mold/op-readiness-checklist.md` (modified, +1/-0)
- `docs/DEVELOPMENT.md` (modified, +2/-0)
- `tests/test_elementwise_independent_fp8.py` (modified, +28/-15)
- `tileops/ops/elementwise.py` (modified, +40/-0)

## `tileops/ops/elementwise.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `tileops/ops/elementwise.py`
