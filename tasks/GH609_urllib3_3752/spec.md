# GH609_urllib3_3752: Patch VerifiedHTTPSConnection for emscripten — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/urllib3/urllib3

## PR Description

<!---
Thanks for your contribution! ♥️

If this is your first PR to urllib3 please review the Contributing Guide:
https://urllib3.readthedocs.io/en/latest/contributing.html

Adhering to the Contributing Guide means we can review, merge, and release your change faster! :)
--->

There is always some downstream project relying on outdated names, in this case `botocore`. With this fix it also gets to use the patched https connection for emscripten

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
