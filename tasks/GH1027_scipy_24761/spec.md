# GH1027_scipy_24761: BUG: `from_rotvec` read-only support — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/scipy/scipy

## PR Description

* Follow up to gh-24753 requested by Evgeni. Similar to the approach in that PR, this patch sets a Cython memoryview to `const` so that it may additionally accept read-only buffers, allowing the new regression test to pass.

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
