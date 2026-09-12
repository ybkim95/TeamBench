# Reference solution — GH291_bookwyrm_3710

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH291_bookwyrm_3710`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH291_bookwyrm_3710/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `bookwyrm/management/commands/fix_isbn10_entries.py` (added, +28/-0)
- `bookwyrm/migrations/0219_datamigration_fix_isbn10_20251017_1810.py` (added, +24/-0)
- `bookwyrm/models/book.py` (modified, +15/-13)
- `bookwyrm/tests/models/test_book_model.py` (modified, +15/-1)

## `bookwyrm/management/commands/fix_isbn10_entries.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `bookwyrm/migrations/0219_datamigration_fix_isbn10_20251017_1810.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `bookwyrm/models/book.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `bookwyrm/management/commands/fix_isbn10_entries.py`
- `bookwyrm/migrations/0219_datamigration_fix_isbn10_20251017_1810.py`
- `bookwyrm/models/book.py`
