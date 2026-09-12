# GH27_pydantic_12907: Add `ascii_only` option to `StringConstraints` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12300
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [x] I have searched Google & GitHub for similar requests and couldn't find anything
- [x] I have read and followed [the docs](https://docs.pydantic.dev) and still think this feature is missing

### Description

I was recently asked for a way to require ascii-only text, and couldn't see anything better than requiring a regex accepting the ascii charset range in `StringConstraints`.

I would think that an `ascii_only` option (name to be bikeshed) would be more user-friendly. It's potentially also possible to check for ascii-only characters a lot cheaper without using a regex.

### Affected Components

- [ ] [Compatibility between releases](https://docs.pydantic.dev/changelog/)
- [x] [Data validation/parsing](https://docs.pydantic.dev/concepts/models/#basic-model-usage)
- [ ] [Data serialization](https://docs.pydantic.dev/concepts/serialization/) - `.model_dump()` and `.model_dump_json()`
- [ ] [JSON Schema](https://docs.pydantic.dev/concepts/json_schema/)
- [ ] [Dataclasses](https://docs.pydantic.dev/concepts/dataclasses/)
- [ ] [Model Config](https://docs.pydantic.dev/concepts/config/)
- [ ] [Field Types](https://docs.pydantic.dev/api/types/) - adding or changing a particular data type
- [ ] [Function validation decorator](https://docs.pydantic.dev/concepts/validation_decorator/)
- [ ] [Generic Models](https://docs.pydantic.dev/concepts/models/#generic-models)
- [ ] [Other Model behaviour](https://docs.pydantic.dev/concepts/models/) - `model_construct()`, pickling, private attributes, ORM mode
- [ ] [Plugins](https://docs.pydantic.dev/) and integration with other tools - mypy, FastAPI, python-devtools, Hypothesis, VS Code, PyCharm, etc.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi, I would like to work on this issue

### Comment 2 ([user]):

[user] go for it, this will need a first step of implementation in `pydantic-core` 👍

## PR Review Comments

**[user]** on `pydantic-core/tests/validators/test_string.py`:

Please remove

**[user]** on `tests/test_types.py`:

```suggestion
def test_string_constraints_ascii_only() -> None:
    class Model(BaseModel):
        v: Annotated[str, StringConstraints(ascii_only=True)]

    assert Model(v='hello').v == 'hello'
    with pytest.raises(ValidationError) as exc_info:
        Model(v='caf\xe9')
    assert exc_info.value.errors(include_url=False)[0] == {
        'type': 'string_not_ascii',
        'loc': ('v',),
        'msg': 'String should contain only ASCII characters',
        'input': 'caf\xe9',
    }
```

**[user]** on `docs/api/standard_library_types.md`:

```suggestion
These constraints can be provided using the [`StringConstraints`][pydantic.types.StringConstraints] metadata type, or using the [`Field()`][pydantic.Field] function (except for `strip_whitespace`, `to_upper`, `to_lower` and `ascii_only`).
```

**[user]** on `docs/api/standard_library_types.md`:

updated, Thanks.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
