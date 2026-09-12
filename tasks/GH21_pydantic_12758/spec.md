# GH21_pydantic_12758: Try other branches in smart union in case of omit errors — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/12750
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [x] I confirm that I'm using Pydantic V2

### Description

Copied from https://github.com/pydantic/pydantic-core/issues/1900

I believe the below test should pass:

```python
def test_td_smart_union_omit() -> None:
    validator = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(
                    core_schema.union_schema(
                        [
                            core_schema.with_default_schema(core_schema.int_schema(), on_error='omit'),
                            core_schema.with_default_schema(core_schema.bool_schema(), on_error='omit'),
                        ]
                    )
                )
            },
        )
    )
    assert validator.validate_python({'x': '123'}) == {'x': 123}
```

but instead it currently fails with 

```python
AssertionError: assert {} == {'x': 123}
```

AFAICT, `'on_error': 'raise'` works as expected.

Setting union mode to `'left_to_right'` passes the test on primary.

```python
def test_td_smart_union_omit() -> None:
    validator = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(
                    core_schema.union_schema(
                        [
                            core_schema.with_default_schema(core_schema.int_schema(), on_error='omit'),
                            core_schema.with_default_schema(core_schema.bool_schema(), on_error='omit'),
                        ],
                        mode='left_to_right'
                    )
                )
            },
        )
    )
    assert validator.validate_python({'x': '123'}) == {'x': 123}
```

So my guess would be [`UnionValidator.validate_smart` in `union.rs`](https://github.com/pydantic/pydantic-core/blob/383eb95a19433754c0cecf7025b50c26b6d97a36/src/validators/union.rs#L103) only looking for LineErrors when adjusting the exactness is the issue. Happy to submit a PR - hopefully not too complex to fix.

Thank you!

### Example Code

```Python
def test_td_smart_union_omit() -> None:
    validator = SchemaValidator(
        core_schema.typed_dict_schema(
            fields={
                'x': core_schema.typed_dict_field(
                    core_schema.union_schema(
                        [
                            core_schema.with_default_schema(core_schema.int_schema(), on_error='omit'),
                            core_schema.with_default_schema(core_schema.bool_schema(), on_error='omit'),
                        ]
                    )
                )
            },
        )
    )
    assert validator.validate_python({'x': '123'}) == {'x': 123}
```

### Python, Pydantic & OS Version

```Text
pydantic version: 2.12.5
        pydantic-core version: 2.41.5
          pydantic-core build: profile=release pgo=false
               python version: 3.11.13 (main, Sep  2 2025, 14:20:25) [Clang 20.1.4 ]
                     platform: Linux-6.8.0-1045-gcp-x86_64-with-glibc2.35
             related packages: pydantic-extra-types-2.11.0 mypy-1.14.1 email-validator-2.3.0 typing_extensions-4.15.0 fastapi-0.128.0 pydantic-settings-2.12.0
                       commit: unknown
```

## PR Review Comments

**[user]** on `pydantic-core/tests/validators/test_union.py`:

Please add a test for when we have `list[int | bool]` with the same `on_error='omit'` clauses on the validators, and an invalid string is passed. We should make sure that case does not regress.

**[user]** on `pydantic-core/tests/validators/test_union.py`:

Thanks! added :)

**[user]** on `pydantic-core/tests/validators/test_union.py`:

Just looking at the code, omitted members should not contribute to the max length, so let's add a limit to make sure that remains ok.

```suggestion
            ),
            max_length=2,
```

**[user]** on `pydantic-core/src/validators/union.rs`:

I think we can just keep a boolean marker, looks like the labels are never used:

```suggestion
        // propagate an omit error if all branches failed
        let mut should_omit = true;
```

**[user]** on `pydantic-core/tests/validators/test_union.py`:

Would it be possible to have pydantic tests instead? That is, have a proper `TypedDict` defined, and use `TypeAdapter` to make the assertions?

In this case, it would look like:

```python
class TD(TypedDict):
    x: OnErrorOmit[int] | OnErrorOmit[str]
```

I'm also wondering if this should be valid at all. If you simply do:

```python
class TD(TypedDict):
    x: OnErrorOmit[int | bool]  # or even just OnErrorOmit[int]
```

We get a schema build error:

```python
TypeAdapter(TD)
"""
pydantic_core._pydantic_core.SchemaError: Error building "typed-dict" validator:
  SchemaError: Field 'x': 'on_error = omit' cannot be set for required fields
"""
```

And doing this works fine:

```python
class TD(TypedDict, total=False):
    x: OnErrorOmit[int | bool]

ta = TypeAdapter(TD)

ta.validate_python({'x': '123'})
#> {'x': 123}
```

So presumably we're not catching a schema build error when doing `OnErrorOmit[int] | OnErrorOmit[str]`, which leads to inconsistent validation results?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
