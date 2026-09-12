# GH965_pymc_8201: Fix off-by-one progress bar bugs — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pymc-devs/pymc

## PR Description

Progress bar is currently off by one when it completes, and [user] is bullying me about it. The issue was we added a `-1` factor to the total at some point when we shouldn't have. This caused the samplers to stop at `n-1 / n` (for which I was bullied). In the case of SMC sampling, it caused the progressbar maximum to be 0, so progress immediately stopped and no timing info is given.

I also re-wrote the test_manager tests. They weren't testing anything, just type checks and deterministic code paths. I added some tests that would have caught these off-by-one bugs.

I also simplified the `is_last` logic. Previously it was trying to calculate the remaining steps then advancing by that much, then doing a cleanup step. Now we just directly set the total completed to the expected total. This should be 100% bulletproof against embarrassing off-by-one bugs.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
