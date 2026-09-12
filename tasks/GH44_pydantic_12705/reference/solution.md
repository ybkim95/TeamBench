# Reference solution — GH44_pydantic_12705

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH44_pydantic_12705`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH44_pydantic_12705/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `pydantic/_internal/_generate_schema.py` (modified, +16/-1)
- `pydantic/functional_validators.py` (modified, +2/-2)
- `tests/test_types.py` (modified, +18/-3)

## `pydantic/_internal/_generate_schema.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `pydantic/functional_validators.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `pydantic/_internal/_generate_schema.py`
- `pydantic/functional_validators.py`
