# GH711_celery_10187: pep 649 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/celery/celery

## PR Description

(withheld: the upstream fix is not part of the task) only partially addressed head_from_fun and _task_from_fun, but left fun_accepts_kwargs still using inspect.signature which triggers PEP 649 annotation evaluation.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
