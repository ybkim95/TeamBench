# GH158_attrs_1529: Add instance support to attrs.fields() — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/python-attrs/attrs/issues/1400
- Repo: https://github.com/python-attrs/attrs

## Issue Description

Unless I am mistaken, one cannot use `attrs.fields` on a attrs class object, unlike `attrs.has`. The workaround is simple, either `attrs.fields(type(obj))` or `obj.__attrs_attrs__`. It would be nice to be able to use `attrs.fields` directly.

```python

@attrs.define
class Hello():
    a = attrs.field()
    b = attrs.field()

# This works
attrs.fields(Hello)

# But this doesn't (yet)
attrs.fields(Hello(1, 2))

# NB: this works though
attrs.has(Hello)
attrs.has(Hello(1, 2))

```

Thanks for the awesome library

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Great, thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
