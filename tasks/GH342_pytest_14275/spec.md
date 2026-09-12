# GH342_pytest_14275: fixtures: a couple of bug fixes for `pytest_fixture_post_finalizer` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

These are changes extracted from [user]'s PR #14104. That PR is big, so I decided to split this part so we can have a focused discussion and decision on these particular changes, and then #14104's can be a bit smaller.

The first test only adds a failing (xfail) test for #5848, that is that `pytest_fixture_post_finalizer` is sometimes called twice for the same teardown. I think this is definitely undesirable. We *could* state that `pytest_fixture_post_finalizer` needs to be idempotent and be prepared to be called multiple times, but I don't see any reason for that. It's also somewhat wasteful.

The second commit is not from [user]'s PR, but just fixes the above problem in the most direct way, namely to do an early exit if already finished (`cached_result` is `None`). There is a possible gotcha here is somehow `addfinalizer` is called after `finish`, but I'm pretty sure this can't happen. Would have added an assert but it's not easy I think. I think this is good change anyway to avoid uselessly running the `finish` code when it will have no effect (well, except the `pytest_fixture_post_finalizer` call).

The third commit is [user]'s different clever fix for the problem and also for another issue #14114 that things aren't handled gracefully if `pytest_fixture_post_finalizer` raises. I'm not a 100% on this:
1. I think the `pytest_fixture_post_finalizer` is not very realistic, generally if hooks raise it's not something we *really* try to handle, it's basically a broken plugin. I think this is also what [user] mean in the issue.
2. The solution of making it a finalizer is a bit of a semantic mixup.
However, I think handling it is still nice, and the semantics can make sense from a certain perspective. So it has my approval..

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
