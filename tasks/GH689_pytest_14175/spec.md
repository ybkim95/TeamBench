# GH689_pytest_14175: [pre-commit.ci] pre-commit autoupdate — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pytest-dev/pytest

## PR Description

<!--pre-commit.ci start-->
updates:
- [github.com/astral-sh/ruff-pre-commit: v0.14.14 → v0.15.4](https://github.com/astral-sh/ruff-pre-commit/compare/v0.14.14...v0.15.4)
- github.com/tox-dev/pyproject-fmt: v2.12.1 → v2.12.1 our fork which won't change

## PR Review Comments

**[user]** on `pyproject.toml`:

Double escaping seems rough.. Can we make it keep using raw-strings?

**[user]** on `pyproject.toml`:

I'd rather move this to a `towncrier.toml` than have this weird formatting..

**[user]** on `pyproject.toml`:

🙈

**[user]** on `pyproject.toml`:

pyproject-fmt gets more and more developer-hostile. i started to drop it from projects as ever since 2.x it messes up more and more things

**[user]** on `pyproject.toml`:

Let's freeze it ? Might need to fork it so it's not upgraded automatically by pre-commit

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
