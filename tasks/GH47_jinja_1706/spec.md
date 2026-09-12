# GH47_jinja_1706: Improve the PackageLoader error message — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pallets/jinja/issues/1705
- Repo: https://github.com/pallets/jinja

## Issue Description

When following [the basics of setting up jinja2](https://jinja.palletsprojects.com/en/3.1.x/api/#basics), if you don't create the appropriate `templates` directory in your package, you get this error message:

```
ValueError: The 'mypackage' package was not installed in a way that PackageLoader understands.
```

This could be significantly improved by explaining the actual problem: The PackageLoader could not find a suitable "templates" directory.

To replicate, add this to `mypackage.py`:

```python
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader("mypackage"))
```

If you run `python mypackage.py` you will see a traceback similar to this:

```python
Traceback (most recent call last):
  File "mypackage/mypackage.py", line 4, in <module>
    env = Environment(loader=PackageLoader("mypackage"))
  File ".virtualenvs/mypackage/lib/python3.10/site-packages/jinja2/loaders.py", line 291, in __init__
    import_module(package_name)
  File ".pyenv/versions/3.10.3/lib/python3.10/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1050, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1027, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1006, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 688, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 883, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "mypackage/mypackage.py", line 4, in <module>
    env = Environment(loader=PackageLoader("mypackage"))
  File ".virtualenvs/mypackage/lib/python3.10/site-packages/jinja2/loaders.py", line 323, in __init__
    raise ValueError(
ValueError: The 'mypackage' package was not installed in a way that PackageLoader understands.

```

Seeing an error message that explained that jinja2 couldn't find an appropriate "templates" directory would be much better.

Environment:

- Python version: 3.10.3
- Jinja version: 3.1.2

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Happy to review a PR.

## PR Review Comments

**[user]** on `src/jinja2/loaders.py`:

I think the original message was about not being able to find the package properly. i.e. At line 315, `roots` would still be an empty list, because it failed to find anything.

So, it seems better to me if the original error is raised if `roots` is empty, otherwise raise this new error message if we don't break from the loop (i.e. add an `else` to the `for` loop).

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
