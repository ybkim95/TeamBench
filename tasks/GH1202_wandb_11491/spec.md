# GH1202_wandb_11491: fix(artifacts): reseed random state for client IDs on fork — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

## JIRA Issue(s)

Fixes https://wandb.atlassian.net/browse/WB-29707

## Description

PR fixes artifact client ID generation in forked child processes.

- Reseeds the dedicated fast RNG used for artifact client IDs after `fork()`.
- Prevents parent and child processes from inheriting identical RNG state and generating colliding client IDs.
- Keeps the existing fast non-cryptographic ID path while making it safe across process forks.

## Testing

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
