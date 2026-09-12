# GH537_redis-py_3976: Removed attributes from recorders — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/redis/redis-py

## PR Description

### Description of change

_Please provide a description of the change here._

### Pull Request check-list

_Please make sure to review and check all of these items:_

- [ ] Do tests and lints pass with this change?
- [ ] Do the CI tests pass with this change (enable it first in your forked repo and wait for the github action build to finish)?
- [ ] Is the new or changed code fully tested?
- [ ] Is a documentation update included (if this change modifies existing APIs, or introduces new ones)?
- [ ] Is there an example added to the examples folder (if applicable)?

_NOTE: these things are not required to open a PR and can be done
afterwards / while the PR is open._

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
