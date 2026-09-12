# Reference solution — GH20_pydantic_12748

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH20_pydantic_12748`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH20_pydantic_12748/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/concepts/fields.md` (modified, +12/-8)
- `pydantic-core/python/pydantic_core/core_schema.py` (modified, +13/-2)
- `pydantic-core/src/serializers/computed_fields.rs` (modified, +3/-2)
- `pydantic/_internal/_generate_schema.py` (modified, +7/-1)
- `pydantic/fields.py` (modified, +6/-0)
- `tests/test_computed_fields.py` (modified, +40/-1)

## `pydantic-core/python/pydantic_core/core_schema.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `pydantic/_internal/_generate_schema.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `pydantic/fields.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `pydantic-core/python/pydantic_core/core_schema.py`
- `pydantic/_internal/_generate_schema.py`
- `pydantic/fields.py`
