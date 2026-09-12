# GH20_pydantic_12748: Support `exclude_if` in computed fields — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12690
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

The new `exclude_if` annotation in `Field` is ignored on `computed_fields`.

I am not sure if this is similar to or completely different from the other issue (https://github.com/pydantic/pydantic/issues/12387).  It seems like it's different enough I decided to open a new issue.

### Example Code

```Python
from pydantic import BaseModel, Field
from typing import Annotated

IntExcludeZero = Annotated[int, Field(exclude_if=lambda v: v == 0)]

class Model(BaseModel):
    @computed_field
    def a_computed_field(self) -> IntExcludeZero:
        return 0

obj = Model()
print(obj.model_dump())  # {"a_computed_field": 0 }
```

The expected behavior for the code above  is for `a_computed_field` to not be in the result due to the `exclude_if` directive.

### Python, Pydantic & OS Version

```Text
             pydantic version: 2.12.5
        pydantic-core version: 2.41.5
          pydantic-core build: profile=release pgo=false
               python version: 3.10.14 (main, Nov  9 2024, 11:48:33) [Clang 16.0.0 (clang-1600.0.26.4)]
                     platform: macOS-15.7.3-arm64-arm-64bit
             related packages: mypy-1.19.1 typing_extensions-4.15.0
                       commit: unknown
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi! I'm a new open source developer and would like to take on this issue. I'd like to know if this is an open issue, and if so, what behavior would you expect?

### Comment 2 ([user]):

I think this can be handled after (withheld: the upstream fix is not part of the task).

## PR Review Comments

**[user]** on `pydantic/_internal/_generate_schema.py`:

is this status code correct?

**[user]** on `pydantic/_internal/_generate_schema.py`:

I'm not 100% if this is the best way to get the metadata from the annotated field for this use case. I've seen this method `self._get_args_resolving_forward_refs` when the process gets the return type schema, but there's no way (correct me if I'm wrong) to forward additional metadata (such as this new `exclude_if`) without modifying the returning schemas (`core.CoreSchema`)

**[user]** on `pydantic/_internal/_generate_schema.py`:

Any recommendation is welcome :)

**[user]** on `pydantic/_internal/_generate_schema.py`:

I'm not sure if this is necessary, in a lot of places I think if there are multiple `FieldInfo` we accept it without complaint. cc [user] ?

**[user]** on `pydantic/_internal/_generate_schema.py`:

I guess that there is a potential alternative here that if two `exclude_if` callables are present, the result is to merge them both and exclude if either of them returns true. But I'm not sure if that's a wise idea.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
