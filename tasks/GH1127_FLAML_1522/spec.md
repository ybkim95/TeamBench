# GH1127_FLAML_1522: Fix test_no_optuna reinstalling optuna at wrong version — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/microsoft/FLAML

## PR Description

## Why are these changes needed?

The `test_no_optuna()` test in `test/tune/test_searcher.py` uninstalls optuna to verify graceful handling when it is missing, then reinstalls it. However, it was hardcoded to reinstall `optuna==2.8.0` instead of using the version range specified elsewhere (`>=2.8.0,<=3.6.1`).

Since this test runs before the "Save dependencies" CI step, `pip freeze` captured the downgraded version, causing the saved dependency snapshot to incorrectly report `optuna==2.8.0` instead of `3.6.1`.

The fix changes the reinstall command from `optuna==2.8.0` to `optuna>=2.8.0,<=3.6.1` so the latest compatible version is restored after the test.

## Related issue number

N/A

## Checks

- [x] I've used [pre-commit](https://microsoft.github.io/FLAML/docs/Contribute#pre-commit) to lint the changes in this PR (note the same in integrated in our CI checks).
- [ ] I've included any doc changes needed for https://microsoft.github.io/FLAML/. See https://microsoft.github.io/FLAML/docs/Contribute#documentation to build and test documentation locally.
- [ ] I've added tests (if relevant) corresponding to the changes introduced in this PR.
- [ ] I've made sure all auto checks have passed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
