# GH48_pydantic_11089: Simplify test parametrization in `test_types_self.py` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/pydantic/pydantic/issues/123
- Repo: https://github.com/pydantic/pydantic

## Issue Description

Implemented what we discussed in #120

Also changed pytest execution in the Makefile (was failing in my machine).

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

# [Codecov](https://codecov.io/gh/samuelcolvin/pydantic/pull/123?src=pr&el=h1) Report
> Merging [#123](https://codecov.io/gh/samuelcolvin/pydantic/pull/123?src=pr&el=desc) into [master](https://codecov.io/gh/samuelcolvin/pydantic/commit/423137cefe091b63166bb0a4531fef8b9c4eaf0a?src=pr&el=desc) will **not change** coverage.
> The diff coverage is `100%`.

[Code changes omitted — Planner should analyze the issue and guide the Executor]

### Comment 2 ([user]):

What kind of documentation are you thinking about? Since it's in the stdlib the documentation is already there: https://docs.python.org/3/library/abc.html

Maybe just a mention in the changelog?

### Comment 3 ([user]):

Just a show section in the main docs saying something like "pydantic works with python's standard abc" then a mini example in python.

### Comment 4 ([user]):

Tests are failing since I readded `pytest-sugar` to the Makefile.

### Comment 5 ([user]):

Looks great. Thank you very much. I'll wait a couple of days in the hope that pytest-sugar gets fixed, if it doesn't I'll remove it.

Once that's done this looks ready to merge.

### Comment 6 ([user]):

great, thank you very much.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
