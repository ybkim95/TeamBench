# GH282_django_20502: Refs #470 -- Fixed further field_defaults test failures due to year-end boundary conditions. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/django/django

## PR Description

Follow-up to 352d860b9107adbcde0f1fe5d0fce8e9090a51e4.

These tests involve a database default making use of `ExtractYear(Now())`, which could be sensitive to timezones around 1/1, which is what happened for the second year in a row, see [logs](https://github.com/django/django/actions/runs/20631778850/job/59250744513):

<details>
<summary>Failure</summary>

```
======================================================================
FAIL: test_bulk_create_mixed_db_defaults_function (field_defaults.tests.DefaultTests.test_bulk_create_mixed_db_defaults_function)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\hostedtoolcache\windows\Python\3.13.11\x64\Lib\unittest\case.py", line 58, in testPartExecutor
    yield
  File "C:\hostedtoolcache\windows\Python\3.13.11\x64\Lib\unittest\case.py", line 651, in run
    self._callTestMethod(testMethod)
    
  File "C:\hostedtoolcache\windows\Python\3.13.11\x64\Lib\unittest\case.py", line 606, in _callTestMethod
    if method() is not None:
    ^^^^^^^^^^^^^^^
  File "D:\a\django\django\django\test\testcases.py", line 1588, in skip_wrapper
    return test_func(*args, **kwargs)
    ^^^^^^^
  File "D:\a\django\django\django\test\utils.py", line 458, in inner
    return func(*args, **kwargs)
    ^^^
  File "D:\a\django\django\tests\field_defaults\tests.py", line 184, in test_bulk_create_mixed_db_defaults_function
    self.assertCountEqual(years, [2000, timezone.now().year])
    ^^^^^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.13.11\x64\Lib\unittest\case.py", line 1238, in assertCountEqual
    self.fail(msg)
    ^^^^^^^^^^^
  File "C:\hostedtoolcache\windows\Python\3.13.11\x64\Lib\unittest\case.py", line 732, in fail
    raise self.failureException(msg)
    ^^^^^^^^^^^^^^^
AssertionError: Element counts were not equal:
First has 1, Second has 0:  2025
First has 0, Second has 1:  2026

----------------------------------------------------------------------
Ran 18919 tests in 259.254s
```
</details>

Overriding `USE_TZ=True` during a test creates drift between the SQL compiled for inserted values versus the deployed database default, as `Extract()` inquires of the current timezone:

https://github.com/django/django/blob/c68e4adea0703354508d51895b091771b1f6ac45/django/db/models/functions/datetime.py#L56-L57

To resolve this, leave `USE_TZ=False` and make UTC explicit when asserting over the result.

***
The reason only one of the two tests I touched last time in #18983 is not working is due to a behavior difference between `create()` and `bulk_create()` discussed at greater length at (withheld: the upstream fix is not part of the task)#issuecomment-3715528301, which I will probably turn into a forum post to sound out.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
