# GH570_urllib3_3755: Fix Scorecard issues related to vulnerable dev dependencies — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/urllib3/urllib3

## PR Description

[Our OpenSSF score](https://deps.dev/pypi/urllib3/2.6.2) was lowered because of pinned dev dependencies with vulnerabilities

<img width="400" alt="image" src="https://github.com/user-attachments/assets/88257b43-7471-47bb-9e50-3361eea899ea" />

In this PR, I upgrade the three dependencies and add `osv-scanner.toml` to ignore the dev dependencies.

This is the result with and without the new configuration file before I upgraded the dependencies:

<img width="1594" height="815" alt="image" src="https://github.com/user-attachments/assets/9edbc01a-e375-4f5f-94fe-096ebeda8dd5" />

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
