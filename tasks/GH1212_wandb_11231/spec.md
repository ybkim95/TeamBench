# GH1212_wandb_11231: fix: authenticate in wandb beta sync — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/wandb/wandb

## PR Description

Fixes `wandb beta sync` which currently fails to load credentials.

Tests didn't catch this because they propagate credentials through environment variables like `WANDB_API_KEY`. I added a `wbauth.unauthenticate_session()` to a test to catch this in the future.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
