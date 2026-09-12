# GH590_aiohttp_11757: [pre-commit.ci] pre-commit autoupdate — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/aio-libs/aiohttp

## PR Description

<!--pre-commit.ci start-->
updates:
- [github.com/PyCQA/isort: 7.0.0 → 8.0.1](https://github.com/PyCQA/isort/compare/7.0.0...8.0.1)
- [github.com/psf/black-pre-commit-mirror: 25.9.0 → 26.3.1](https://github.com/psf/black-pre-commit-mirror/compare/25.9.0...26.3.1)
- [github.com/asottile/pyupgrade: v3.21.0 → v3.21.2](https://github.com/asottile/pyupgrade/compare/v3.21.0...v3.21.2)
- [github.com/codespell-project/codespell: v2.4.1 → v2.4.2](https://github.com/codespell-project/codespell/compare/v2.4.1...v2.4.2)
<!--pre-commit.ci end-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
