# GH1108_pytorch_163861: fix pickling for BitwiseFn — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pytorch/pytorch/issues/147841
- Repo: https://github.com/pytorch/pytorch

## Issue Description

### 🐛 Describe the bug

I encountered an issue while trying to pickle an instance of a dynamically generated class using `make_opaque_bitwise_fn` from `torch.utils._sympy.functions`.

```
import pickle
import sympy
from torch.utils._sympy.functions import make_opaque_bitwise_fn

# Generate the bitwise_and function class
BitwiseFn_bitwise_and = make_opaque_bitwise_fn("bitwise_and", "and_")

# Create an instance of the dynamically generated class
x = BitwiseFn_bitwise_and(sympy.Symbol('a'), sympy.Symbol('b'))
data = pickle.dumps(x)
```

# Output
```
AttributeError: Can't pickle local object 'make_opaque_bitwise_fn.<locals>.BitwiseFn'
```

# Similar PR
(withheld: the upstream fix is not part of the task)


### Versions

torch 2.6.0

cc [user] [user] [user] [user]

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Removing the pt2 tag since it has nothing to do with torch.compile.

### Comment 2 ([user]):

This can be fixed by manually rewriting the `__name__` on the generated class. I vaguely recall fixing this, actually, so someone should check the repro before working on this.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
