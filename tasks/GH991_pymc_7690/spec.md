# GH991_pymc_7690: Fix bug with chained CustomSymbolicDists — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pymc-devs/pymc

## PR Description

Reported in https://discourse.pymc.io/t/error-with-custom-distribution-after-using-scan/16255

<!-- readthedocs-preview pymc start -->
----
📚 Documentation preview 📚: https://pymc--7690.org.readthedocs.build/en/7690/

<!-- readthedocs-preview pymc end -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
