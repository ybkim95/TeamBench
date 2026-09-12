# GH1144_wandb_11495: chore: clean up dev requirements and fix bokeh 3.9 serialization issue — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Description
-----------
- Remove `orjson` requirement left in `requirements_dev.txt` after a recent refactor (vendoring a modified orjson) and it was being pulled into version-specific req files.
- Regenerated req files, which pulled in bokeh 3.9 - fixed an associated issue while I was at it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
