# Reference solution — GH218_core_160825

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH218_core_160825`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH218_core_160825/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `homeassistant/components/coolmaster/climate.py` (modified, +3/-1)
- `tests/components/coolmaster/conftest.py` (modified, +39/-0)
- `tests/components/coolmaster/test_climate.py` (modified, +36/-8)
- `tests/components/coolmaster/test_init.py` (modified, +18/-8)

## `homeassistant/components/coolmaster/climate.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

- `homeassistant/components/coolmaster/climate.py`
