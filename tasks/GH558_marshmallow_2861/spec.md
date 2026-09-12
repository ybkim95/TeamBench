# GH558_marshmallow_2861: (fix) missing constant with len validation — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/marshmallow-code/marshmallow

## PR Description

Currently if you utilize the `missing` constant as fallback value for a field in a schema alongside a length validator it fails with the following error `"object of type '_Missing' has no len()`

I'm using missing like this because I have some function fields that parse some optional data (in an annoying list of dictionaries), and if you include a standard pythonic default value of `None, [], {}, ""` the blank field is still included in `load()` results instead of being excluded, where as if you use missing it gets dropped from result as expected. 

If you'd like to know more about my use case or my schema just let me know

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
