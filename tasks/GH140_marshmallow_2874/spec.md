# GH140_marshmallow_2874: Fix: Case sensitivity in validator — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/marshmallow-code/marshmallow/issues/2870
- Repo: https://github.com/marshmallow-code/marshmallow

## Issue Description

`marshmallow.validate.URL` lowercases the scheme parsed from the input, but it stores the user-provided schemes iterable as-is. When a caller supplies uppercase or mixed-case schemes (e.g. ["A"]), validation always fails: the parsed scheme becomes "a", which isn’t found in ["A"], and the validator raises ValidationError: "Not a valid URL.".

```python
from marshmallow.validate import URL
from marshmallow import ValidationError

validator = URL(schemes=["A"])  # custom scheme in uppercase

validator("A://example.com")
```

```
Traceback (most recent call last):
  File "/data/src/test.py", line 6, in <module>
    validator("A://example.com")
  File "/home/hdd/miniconda3/envs/py312/lib/python3.12/site-packages/marshmallow/validate.py", line 209, in __call__
    raise ValidationError(message)
marshmallow.exceptions.ValidationError: Not a valid URL.
```

> Note: This issue was identified by an automated testing tool for academic research and manually verified. If you have any concerns about this type of reporting, please let me know, and I will adjust my workflow accordingly.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'm not sure on this one. Are there cases where the case-sensitivity might be desired 🤔 ? seems plausible

### Comment 2 ([user]):

Thanks for your response. I just thought the current behavior was just a bit confusing that the validator lowercases the input but checks it against the raw list.

### Comment 3 ([user]):

I agree it would make sense to also lowercase the schemes. I'd consider this a bugfix.

Would you like to send a PR?

### Comment 4 ([user]):

Sure. I will send a PR later.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
