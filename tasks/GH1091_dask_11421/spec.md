# GH1091_dask_11421: Add cupy support for indexed assignment — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/dask/dask

## PR Description

Minor fix to `parse_assignment_indices` in `dask.array`: Generalizes the `np.ndarray` instance check to use `is_arraylike`.

- [x] Closes [#xxxx](https://github.com/dask/dask/issues/11266)
- [ ] Tests added / passed
- [ ] Passes `pre-commit run --all-files`

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
