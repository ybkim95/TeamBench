# Reference solution — GH548_ruff_14098

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH548_ruff_14098`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH548_ruff_14098/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `crates/ruff_linter/resources/test/fixtures/refurb/FURB157.py` (modified, +20/-0)
- `crates/ruff_linter/src/rules/refurb/rules/verbose_decimal_constructor.rs` (modified, +36/-5)
- `crates/ruff_linter/src/rules/refurb/snapshots/ruff_linter__rules__refurb__tests__FURB157_FURB157.py.snap` (modified, +40/-0)

## Moved from `brief.md`

## Files That May Need Changes

- (see workspace)
