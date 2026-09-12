# GH1058_ray_15056: fix setproctitle break /proc/PID/environ — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/ray-project/ray

## PR Description

## Why are these changes needed?

Ray use setproctitle to  change python worker process title, the process's /proc/PID/environ will be cleared.

The root cause is:  the setproctitle lib will reset process title and unfortunately breaks /proc/PID/environ.

According to https://github.com/dvarrazzo/py-setproctitle#environment-variables, add "SPT_NOENV" env to prevent setproctitle clearing /proc/PID/environ

## Related issue number

https://github.com/ray-project/ray/issues/15061

## Checks

- [ ] I've run `scripts/format.sh` to lint the changes in this PR.
- [ ] I've included any doc changes needed for https://docs.ray.io/en/master/.
- [ ] I've made sure the tests are passing. Note that there might be a few flaky tests, see the recent failures at https://flakey-tests.ray.io/
- Testing Strategy
   - [x] Unit tests
   - [ ] Release tests
   - [ ] This PR is not tested :(

## PR Review Comments

**[user]** on `python/ray/__init__.py`:

Remove these  lines?

**[user]** on `python/ray/__init__.py`:

Have remove these.

**[user]** on `python/ray/tests/test_environ.py`:

Can we gurantee all of environ variables in os.environ equal to results from /proc/$PID/environ?

**[user]** on `python/ray/tests/test_environ.py`:

There is no gurantee for that. /proc/$PID/environ will not reflect os.environ changes

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
