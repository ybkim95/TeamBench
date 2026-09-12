# Reference solution — GH288_osparc-simcore_6935

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH288_osparc-simcore_6935`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH288_osparc-simcore_6935/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `services/storage/src/simcore_service_storage/db_file_meta_data.py` (modified, +5/-5)
- `services/storage/src/simcore_service_storage/simcore_s3_dsm.py` (modified, +32/-17)
- `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py` (modified, +5/-0)
- `services/storage/tests/unit/test_db_file_meta_data.py` (modified, +6/-6)
- `services/storage/tests/unit/test_handlers_files.py` (modified, +47/-0)
- `services/storage/tests/unit/test_simcore_s3_dsm_utils.py` (added, +21/-0)

## `services/storage/src/simcore_service_storage/db_file_meta_data.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `services/storage/src/simcore_service_storage/simcore_s3_dsm.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

### `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Moved from `brief.md`

## Files That May Need Changes

        - `services/storage/src/simcore_service_storage/db_file_meta_data.py`
- `services/storage/src/simcore_service_storage/simcore_s3_dsm.py`
- `services/storage/src/simcore_service_storage/simcore_s3_dsm_utils.py`
