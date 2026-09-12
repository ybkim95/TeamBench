# GH156_pyyaml_305: Change default loader for add_implicit_resolver, add_path_resolver — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/yaml/pyyaml/issues/294
- Repo: https://github.com/yaml/pyyaml

## Issue Description

I've noticed that with PyYAML 5.1 implicit resolvers do not seem to work at all. Using this example script:
```python
import re
import uuid
import yaml

regex = re.compile(r'^UUID\((.+)\)$')
yaml.add_implicit_resolver('!uuid', regex)

def convert_uuid(loader, node):
    value = loader.construct_scalar(node)
    str_value = regex.match(value).group(1)
    return uuid.UUID(str_value)

yaml.add_constructor('!uuid', convert_uuid)

print(yaml.load('''
    config:
        abc: UUID(6a02171e-6482-11e9-ab43-f2189845f1cc)
        def: abc
'''))
```
I confirmed that w/ 3.13 we correctly get the `uuid.UUID` object, while it is a string with 5.1 is it just the string `'UUID(6a02171e-6482-11e9-ab43-f2189845f1cc)'`. The way I found this was that it broke the environment variable interpolation that `elasticsearch-curator` provides. 

Sorry if this is a duplicate, I searched around and could not find an equivalent issue.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

After looking around this appears to be the same issue as https://github.com/yaml/pyyaml/issues/266 , I confirmed it does work with `Loader` set. It does seem to be a bug, but I'll close this issue as it's covered there

### Comment 2 ([user]):

[user] I suggest to reopen because `add_implicit_resolver` is not yet covered by the fixes.
(also `add_path_resolver` btw)

### Comment 3 ([user]):

I'm reopening this for [user]

### Comment 4 ([user]):

I created #305 to fix this

### Comment 5 ([user]):

We just released 5.2b1 https://pypi.org/project/PyYAML/5.2b1/ which should fix this.

### Comment 6 ([user]):

We released 5.2: https://pypi.org/project/PyYAML/5.2/

### Comment 7 ([user]):

Closing. Please reopen if necessary. Thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
