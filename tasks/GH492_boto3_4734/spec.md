# GH492_boto3_4734: Add TypeError for bare @requires_crt usage and regression tests — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/boto/boto3

## PR Description

*Background:*
`@requires_crt` is used to skip tests when the optional CRT dependency is not installed. The only supported form should be `@requires_crt()`. Using bare `@requires_crt` is unsafe because `requires_crt` is implemented as a decorator factory. Python passes the test function as the `reason` argument, causing the real test body to never run. Assertions are never evaluated, but the test may still appear to pass or skip silently. 

*Description of changes:*
This PR makes bare `@requires_crt` fail immediately with a `TypeError`. All existing usages in boto3 already use `@requires_crt()` with parentheses.

*Testing:*
Regression tests are added to verify correct behavior. All tests including the new tests pass.

By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice.

## PR Review Comments

**[user]** on `tests/unit/test_crt.py`:

nit - Minor style preference to be consistent with the `is True` above
```suggestion
            assert getattr(my_test, '__unittest_skip__', False) is False
```

**[user]** on `tests/unit/test_crt.py`:

Both description and code updated. Thanks for the suggestion!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
