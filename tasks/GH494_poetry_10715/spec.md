# GH494_poetry_10715: fix: suggest `poetry self lock` for `self` commands — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/python-poetry/poetry

## PR Description

Fixes python-poetry/poetry#10536.

When an install/sync operation is run via `poetry self ...`, the outdated-lock message currently suggests `poetry lock`, which points at the current project rather than Poetry’s system project.

This changes the suggestion to `poetry self lock` when the installer is operating on Poetry’s system project.

Tests:
- `python -m pytest -o addopts= tests/installation/test_installer.py::test_not_fresh_lock_self_project`

## Summary by Sourcery

Adjust installer lock-file guidance to suggest the appropriate command when working on Poetry’s own system project.

Bug Fixes:
- Ensure outdated-lock error messages for Poetry’s system project instruct users to run `poetry self lock` instead of `poetry lock`.

Tests:
- Add coverage verifying that installer errors for the self project recommend `poetry self lock` when the lock file is not fresh.

## PR Review Comments

**[user]** on `src/poetry/installation/installer.py`:

Now, we have two places where the constant is defined. We should define the constant in one place.

**[user]** on `src/poetry/installation/installer.py`:

Addressed in 38d02e44. I moved the system project name to `poetry.utils.constants.POETRY_SYSTEM_PROJECT_NAME` and reused it from `Installer`, `ShowCommand`, `SelfCommand`, and the installer test so the value is defined in one place only.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
