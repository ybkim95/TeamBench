# GH37_pydantic_12816: Ensure `__pydantic_private__` is set in `model_construct()` with user-defined `model_post_init()` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12813
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

## Title

`model_construct()` can leave `__pydantic_private__` unset when `model_post_init` is user-defined, causing `pickle.dumps()` to crash in `BaseModel.__getstate__`

## Environment

- pydantic==2.12.5
- Python 3.13

## Minimal Repro

```python
import pickle
from pydantic import BaseModel

class M(BaseModel):
    x: int

    def model_post_init(self, context):
        # user-defined post-init that does not touch private attrs
        pass

m = M.model_construct(x=1)
print(hasattr(m, "__pydantic_private__"))  # False in this scenario
pickle.dumps(m)  # AttributeError

### Example Code

```Python

```

### Python, Pydantic & OS Version

```Text
pydantic version: 2.12.5
        pydantic-core version: 2.41.5
          pydantic-core build: profile=release pgo=false
               python version: 3.13.3 (main, Apr  9 2025, 04:04:49) [MSC v.1943 64 bit (AMD64)]
                     platform: Windows-11-10.0.26200-SP0
             related packages: email-validator-2.3.0 fastapi-0.128.0 pydantic-extra-types-2.11.0 pydantic-settings-2.12.0 typing_extensions-4.15.0
                       commit: unknown
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi, I'd like to work on this. I'll submit a PR shortly.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
