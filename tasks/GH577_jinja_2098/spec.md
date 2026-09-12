# GH577_jinja_2098: deprecate `__version__` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/jinja

## PR Description

As has been done with the other Pallets projects.

The `__version__` attribute is an old pattern from early in Python packaging. Setuptools eventually made it easier to use the pattern by allowing reading the value from the attribute at build time, and some other build backends have done the same.

However, there's no reason to expose this directly in code anymore. It's usually better to use feature detection (`hasattr`, `try/except`) instead. `importlib.metadata.version("jinja2")` can be used to get the version at runtime in a standard way, if it's really needed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
