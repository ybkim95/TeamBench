# GH42_pydantic_12879: Allow dynamic models created with `create_model()` to be used as annotations in the Mypy plugin — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12031
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [x] I have searched Google & GitHub for similar requests and couldn't find anything
- [x] I have read and followed [the docs](https://docs.pydantic.dev) and still think this feature is missing

### Description

Pydantic provides a way to [create models dynamically](https://docs.pydantic.dev/latest/concepts/models/#dynamic-model-creation) (create_model).
The problem is that mypy always complain about these models:

**a.py content:**
```py
from pydantic import create_model, BaseModel
from pydantic.fields import Field

GeneratedModel = create_model(
    "MyModel",
    some_field=(int, Field(default=0))
)

class MyModel(BaseModel):
    a: int
    model: GeneratedModel
```

`$ mypy a.py`
```
a.py:12: error: Variable "a.GeneratedModel" is not valid as a type  [valid-type]
a.py:12: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases
Found 1 error in 1 file (checked 1 source file)
```

Currently, you are forced to add # type: ignore[valid-type] on each line where this model is used, which is a problem because it adds a lot of noise but also disables the check for all variables in the same line as this type: ignore.

[I've asked in mypy github project](https://github.com/python/mypy/issues/19360) and developers suggested pydantic's mypy plugin could be updated to use `get_dynamic_class_hook` for pydantic's `create_model` use-case.

### Affected Components

- [ ] [Compatibility between releases](https://docs.pydantic.dev/changelog/)
- [ ] [Data validation/parsing](https://docs.pydantic.dev/concepts/models/#basic-model-usage)
- [ ] [Data serialization](https://docs.pydantic.dev/concepts/serialization/) - `.model_dump()` and `.model_dump_json()`
- [ ] [JSON Schema](https://docs.pydantic.dev/concepts/json_schema/)
- [ ] [Dataclasses](https://docs.pydantic.dev/concepts/dataclasses/)
- [ ] [Model Config](https://docs.pydantic.dev/concepts/config/)
- [ ] [Field Types](https://docs.pydantic.dev/api/types/) - adding or changing a particular data type
- [ ] [Function validation decorator](https://docs.pydantic.dev/concepts/validation_decorator/)
- [ ] [Generic Models](https://docs.pydantic.dev/concepts/models/#generic-models)
- [ ] [Other Model behaviour](https://docs.pydantic.dev/concepts/models/) - `model_construct()`, pickling, private attributes, ORM mode
- [x] [Plugins](https://docs.pydantic.dev/) and integration with other tools - mypy, FastAPI, python-devtools, Hypothesis, VS Code, PyCharm, etc.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

I'd like to work on this. Added a `get_dynamic_class_hook` to the mypy plugin so that `create_model()` return values are recognized as proper class types, enabling their use in type annotations, `isinstance()` checks, and function signatures.

PR: #12879

### Comment 2 ([user]):

Awesome! [user] will this be included in 2.13.0's final release ?

## PR Review Comments

**[user]** on `pydantic/mypy.py`:

```suggestion
CREATE_MODEL_FULLNAME = 'pydantic.main.create_model'
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
