# GH38_pydantic_12905: Patch unset attributes with `MISSING` during model serialization with `exclude_unset` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12888
- Repo: https://github.com/pydantic/pydantic

## Issue Description

## Description

`model_dump(exclude_unset=True)` on a model containing a `Union` field produces spurious `PydanticSerializationUnexpectedValue` warnings when a union member has unset fields with defaults.

## Reproduction

```python
from typing import Literal

from pydantic import BaseModel

class Cat(BaseModel):
    type: Literal['cat']
    color: str | None = None  # field with default

class Dog(BaseModel):
    type: Literal['dog']

class Zoo(BaseModel):
    animals: list[Cat | Dog]

cat = Cat(type='cat')
zoo = Zoo(animals=[cat])

# Sanity check: model_dump without exclude_unset works fine
assert zoo.model_dump() == {'animals': [{'type': 'cat', 'color': None}]}

# Sanity check: model_dump(exclude_unset=True) on the Cat alone works fine
assert cat.model_dump(exclude_unset=True) == {'type': 'cat'}

# BUG: model_dump(exclude_unset=True) on the parent Zoo produces warnings
assert zoo.model_dump(exclude_unset=True) == {'animals': [{'type': 'cat'}]}
```

The last line produces:

```
UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue(Expected 2 fields but got 1: Expected `Cat` - serialized value may not be as expected [field_name='animals', ...])
  PydanticSerializationUnexpectedValue(Expected `Dog` - serialized value may not be as expected [field_name='animals', ...])
```

The output is correct, but the warnings are spurious.

## Version info

- **Broken**: pydantic 2.13.0b2 / pydantic-core 2.42.0 (installed from latest on github)
- **Works**: pydantic 2.12.5 / pydantic-core 2.41.5
- Python 3.12

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks, bisected to (withheld: the upstream fix is not part of the task).

### Comment 2 ([user]):

The following diff restores the previous behavior but breaks added tests:

[Code changes omitted — Planner should analyze the issue and guide the Executor]

## PR Review Comments

**[user]** on `pydantic-core/src/serializers/type_serializers/model.rs`:

```suggestion
        // If excluding unset fields, mask any fields not in `__pydantic_fields_set__` with the
        // missing sentinel so that the fields serializer will exclude them from the output.
        // The `GeneralFieldsSerializer` makes sure to exclude the value, so any user-defined
        // serializer won't be called.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
