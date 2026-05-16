# GH139_marshmallow_2894: Fix Constant field rejecting None values during load — Full Specification (Planner Only)

## Source
- PR: https://github.com/marshmallow-code/marshmallow/pull/2894
- Issue: https://github.com/marshmallow-code/marshmallow/issues/2868
- Repo: https://github.com/marshmallow-code/marshmallow

## Issue Description

When that constant is `None`, loading any payload that contains null triggers `ValidationError: Field may not be null`. The stems from the initialization order: `Field.__init__` sets `allow_none` based on the (yet-unknown) `load_default`, and only afterwards `Constant.__init__` assigns the actual constant/load_default.

```python
from marshmallow import Schema, fields

class DemoSchema(Schema):
    # Should always load/dump None, independent of input
    sentinel = fields.Constant(None)

schema = DemoSchema()

assert schema.dump({"sentinel": "anything"})["sentinel"] is None

schema.load({"sentinel": None})
```

```
Traceback (most recent call last):
  File "/data/src/test.py", line 11, in <module>
    schema.load({"sentinel": None})
  File "/home/hdd/miniconda3/envs/py312/lib/python3.12/site-packages/marshmallow/schema.py", line 730, in load
    return self._do_load(
           ^^^^^^^^^^^^^^
  File "/home/hdd/miniconda3/envs/py312/lib/python3.12/site-packages/marshmallow/schema.py", line 938, in _do_load
    raise exc
marshmallow.exceptions.ValidationError: {'sentinel': ['Field may not be null.']}
```

> Note: This issue was identified by an automated testing tool for academic research and manually verified. If you have any concerns about this type of reporting, please let me know, and I will adjust my workflow accordingly.

## Issue Discussion (Root Cause Analysis)

### Comment 1 (@sloria):

Thanks for reporting! I agree the current behavior is unexpected. PRs welcome!

## Files Changed in Fix

- `AUTHORS.rst` (modified, +1/-0)
- `CHANGELOG.rst` (modified, +8/-0)
- `src/marshmallow/fields.py` (modified, +2/-2)
- `tests/test_deserialization.py` (modified, +9/-0)

## `src/marshmallow/fields.py`
[Code changes omitted — Planner should analyze the issue and guide the Executor]

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify the source files listed above (not test files)
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
