# GH46_pydantic_12951: Do not include annotations that are not part of named tuple fields — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/7987
- Repo: https://github.com/pydantic/pydantic

## Issue Description

### Initial Checks

- [X] I confirm that I'm using Pydantic V2

### Description

Since the NamedTuple parameter resolution relies on `typing.get_type_hints`, it produces unexpected results for the parameters. This is because when creating a NamedTuple the constructor is formed from the original annotations, regardless of it being inherited, whereas `get_type_hints` retrieves all type hints including bases. Is this intended behaviour?

Results from code below:
```py
[{'name': 'test',
  'schema': {'metadata': {'pydantic.internal.needs_apply_discriminated_union': False},
             'type': 'str'}},
 {'name': 'test2',
  'schema': {'metadata': {'pydantic.internal.needs_apply_discriminated_union': False},
             'type': 'str'}},
 {'name': 'test3',
  'schema': {'metadata': {'pydantic.internal.needs_apply_discriminated_union': False},
             'type': 'str'}}]
Traceback (most recent call last):
  File "test.py", line 182, in <module>
    Bar(test="test", test2="test2", test3="test3")
TypeError: Foo.__new__() got an unexpected keyword argument 'test3'
```

### Example Code

```Python
from typing import NamedTuple
import pprint

class Foo(NamedTuple):
    test: str
    test2: str

class Bar(Foo):
    test3: str

pprint.pprint(TypeAdapter(Bar).core_schema['arguments_schema']['arguments_schema'])
Bar(test="test", test2="test2", test3="test3")
```

### Python, Pydantic & OS Version

```Text
        pydantic version: 2.4.2 (main branch at 60c5db6e1ea55d4e5fc13234810d513b3b1b03ae)
        pydantic-core version: 2.11.0
          pydantic-core build: profile=release pgo=true
                 install path: /repos/pydantic/pydantic
               python version: 3.12.0 | packaged by conda-forge | (main, Oct  3 2023, 08:43:22) [GCC 12.3.0]
                     platform: Linux
             related packages: mypy-1.1.1 email-validator-2.0.0.post2 typing_extensions-4.7.1 pydantic-extra-types-2.1.0 pydantic-settings-2.0.3
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user],

Thanks for reporting this. `NamedTuple` types don't support inheritance in the same way that other Python classes do. So even if you take out the 
```
pprint.pprint(TypeAdapter(Bar).core_schema['arguments_schema']['arguments_schema'])
```
line, this still fails with the exception you've listed.

Given this, I'm not entirely sure what behavior you're looking for...

### Comment 2 ([user]):

Hi! Sorry! I was trying to show that the schema shows the three fields but it's not possible to construct the namedtuple with the three fields yourself if that make sense

### Comment 3 ([user]):

Ah [user],

That makes sense. Thanks for clarifying. I suppose this isn't intended behavior then. Looks like you've done a bit of research into the source of this issue. Do you have any interest in creating a PR with a fix?

### Comment 4 ([user]):

Sure, I can take a crack at it!

## PR Review Comments

**[user]** on `pydantic/_internal/_generate_schema.py`:

```suggestion
            # Filter annotations to only include fields that are actually in the NamedTuple
            # (as subclassing an existing NamedTuple is not supported yet - see https://github.com/python/typing/issues/427)
            # and use `Any` if no annotation exist (i.e. when using `collections.namedtuple()`).
            annotations = {field_name: annotations.get(field_name, Any) for field_name in namedtuple_cls._fields}
```

**[user]** on `tests/test_types_namedtuple.py`:

```suggestion
    """https://github.com/pydantic/pydantic/issues/7987."""

```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
