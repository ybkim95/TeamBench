# GH278_arrow_1182: #1178: changes to address datetime.utcnow deprecation warning — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/arrow-py/arrow/issues/1178
- Repo: https://github.com/arrow-py/arrow

## Issue Description

Python 3.12 deprecates the use of `datetime.datetime.utcnow`, suggesting instead to use `datetime.datetime.now(datetime.UTC)`.

Example from the `humanize` method:
```
  File "/root/project/my_project/libs/utils.py", line 54, in arrow_humanize
    return time.humanize()
           ^^^^^^^^^^^^^^^
  File "/root/project/.tox/py312/lib/python3.12/site-packages/arrow/arrow.py", line 1150, in humanize
    utc = dt_datetime.utcnow().replace(tzinfo=dateutil_tz.tzutc())
          ^^^^^^^^^^^^^^^^^^^^
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Mind if I took this on? Seems like a fairly straightforward task to get started?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
