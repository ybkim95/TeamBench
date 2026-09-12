# GH54_pydantic_12817: Track extra fields set after init in `model_fields_set` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/11134
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [X] I confirm that I'm using Pydantic V2

### Description

The behaviour of `model_fields_set` is confusing: If I give an extra field at model creation, it is included in `model_fields_set`, but if I set it later, it is not.

My expectation is that `model_fields_set` should always be a subset of `model_fields.keys()` and never include extra items.

### Example Code

```Python
from pydantic import BaseModel, ConfigDict

class MRE(BaseModel):
    model_config = ConfigDict(extra="allow")

    actual_field: int

a = MRE.model_validate({"actual_field": 1, "extra_field": 2})
print(a.model_fields_set)  # {'actual_field', 'extra_field'}
print(a.model_extra)       # {'extra_field': 2}

a.double_extra_field = 3
print(a.model_fields_set)  # {'actual_field', 'extra_field'}
print(a.model_extra)       # {'extra_field': 2, 'double_extra_field': 3}
```

### Python, Pydantic & OS Version

```Text
pydantic version: 2.9.2
        pydantic-core version: 2.23.4
          pydantic-core build: profile=release pgo=false
                 install path: /opt/miniconda3/envs/genie/lib/python3.11/site-packages/pydantic
               python version: 3.11.10 (main, Oct  3 2024, 02:26:51) [Clang 14.0.6 ]
                     platform: macOS-14.7-arm64-arm-64bit
             related packages: typing_extensions-4.12.2
                       commit: unknown
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user],

Thanks for your question and the MRE :)

The [docs](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_fields_set) state:

> Returns the set of fields that have been explicitly set on this model instance.

Thus, `model_fields_set` includes extra attributes set as well. That being said, the following is inconsistent:

```py
from pydantic import BaseModel, ConfigDict

class MRE(BaseModel):
    model_config = ConfigDict(extra="allow")

    actual_field: int
    actual_field_optional: int | None = None

a = MRE.model_validate({"actual_field": 1, "extra_field": 2})
print(a.model_fields_set)  # {'actual_field', 'extra_field'}
print(a.model_extra)       # {'extra_field': 2}

a.double_extra_field = 3
print(a.model_fields_set)  # {'actual_field', 'extra_field'}
print(a.model_extra)       # {'extra_field': 2, 'double_extra_field': 3}

a.actual_field_optional = 4
print(a.model_fields_set)  # {'actual_field', 'actual_field_optional', 'extra_field'}
print(a.model_extra)       # {'extra_field': 2, 'double_extra_field': 3}
```

So, I'll classify this as a bug. I'm guessing we should include extra values across the board, even when set after init.

### Comment 2 ([user]):

> The [docs](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_fields_set) state:
> > Returns the set of fields that have been explicitly set on this model instance.

My understanding was that this means "model fields" and does not include extras. Perhaps the doc could also be clarified.

### Comment 3 ([user]):

Want to add on a simular issue with `extra` arg in `ConfigDict`. If updated after the model is defined, the changes don't take and silently fail.

I assume this is because the model is compiled at some point for speed, but is there a way to force re-compilation?

### Comment 4 ([user]):

> Want to add on a simular issue with `extra` arg in `ConfigDict`. If updated after the model is defined, the changes don't take and silently fail.
> 
> I assume this is because the model is compiled at some point for speed, but is there a way to force re-compilation?

Exactly, mutating the configuration after a model is defined isn't a supported pattern.

## PR Review Comments

**[user]** on `pydantic/main.py`:

This isn't necessary.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
