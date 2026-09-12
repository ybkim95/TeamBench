# GH1186_featuretools_2052: Temporarily skip Dask test for test_normalize_with_invalid_time_index in test_es.py due to different error message in WW 0.16.3 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/alteryx/featuretools

## PR Review Comments

**[user]** on `.github/workflows/unit_tests_with_woodwork_main_branch.yml`:

Extra spaces?

**[user]** on `.github/workflows/unit_tests_with_woodwork_main_branch.yml`:

![image](https://user-images.githubusercontent.com/4307001/166829893-95184edf-9132-4887-9fc0-944f90388594.png)

**[user]** on `.github/workflows/unit_tests_with_woodwork_main_branch.yml`:

I don't think we need `--upgrade` if we are using `--force-reinstall`

**[user]** on `.github/workflows/unit_tests_with_woodwork_main_branch.yml`:

Removed

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
