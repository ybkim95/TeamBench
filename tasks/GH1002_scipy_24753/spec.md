# GH1002_scipy_24753: BUG: Rotation.apply read-only memoryview support — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

* Fixes gh-24751.

* A runtime error was possible when feeding in read-only NumPy arrays to `apply()`. Since `const` Cython memoryview arguments can accept both read-only and writeable buffers, the regression test passes after the patch is applied.

#### AI Generation Disclosure

No AI tools used

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
