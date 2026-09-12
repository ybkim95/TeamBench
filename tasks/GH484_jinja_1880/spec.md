# GH484_jinja_1880: improve annotations for methods returning copies — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/jinja

## PR Description

These methods always return a new object of the same type as the object they are bound to, even if this is a subclass. Change the annotations to reflect that.

I have not opened an issue, because it's not a functional bug. It just causes issues with static type checkers.

<!--
Ensure each step in CONTRIBUTING.rst is complete by adding an "x" to each box below.

If only docs were changed, these aren't relevant and can be removed.
-->

Checklist:

- [ ] Add tests that demonstrate the correct behavior of the change. Tests should fail without the change. (N/A)
- [ ] Add or update relevant docs, in the docs folder and in code.  (N/A)
- [x] Add an entry in `CHANGES.rst` summarizing the change and linking to the issue.
- [ ] Add `.. versionchanged::` entries in any relevant code docs. (N/A)
- [x] Run `pre-commit` hooks and fix any issues.
- [x] Run `pytest` and `tox`, no tests failed.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
