# GH416_pytest_14290: fixtures: remove dirty optimization for `request.getfixturevalue()` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

Currently for each `Function` we copy the `FunctionDefinition`'s
`_arg2fixturedefs`. This is done due to an ineffective optimization for
a dynamic `request.getfixturevalue()` when the fixture name wasn't
statically requested. In this case, we would save the dynamically-found
`FixtureDef` in `_arg2fixturedef`, such that if it is requested again in
the same item, it is returned immediately instead of doing a
`_matchfactories` check again. But this case is already covered by the
`_fixture_defs` optimization.

I've always disliked this copy and mutation. The `_arg2fixturedefs`
shenanigans performed during collection are hard enough to follow, and
this only adds to the complexity, due to the mutability and having
multiple different `_arg2fixturedefs` with different contents.

So summing up:

Pros: faster repeated `request.getfixturevalue()` in same test (ineffective)
Cons: complexity (reasoning about mutability), extra copy

Even without the `_fixture_defs` optimization, since
`request.getfixturevalue()` is mostly a last-resort thing, so shouldn't
be too common, and *repeated* calls to it in the same test should be
even less common, and if so `_matchfactories` shouldn't be *that* slow,
it should be fine to remove it.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
