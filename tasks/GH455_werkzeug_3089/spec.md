# GH455_werkzeug_3089: fix parsing last newline in multipart data — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/pallets/werkzeug

## PR Description

The search for the last newline should be after the data_start as without this it may return a newline before the data_start and break subsequent parsing (as seen for multiparts with multiple parts and chunked data).

<!--
Before opening a PR, open a ticket describing the issue or feature the
PR will address. An issue is not required for fixing typos in
documentation, or other simple non-code changes.

Replace this comment with a description of the change. Describe how it
addresses the linked ticket.
-->

<!--
Link to relevant issues or previous PRs, one per line. Use "fixes" to
automatically close an issue.

fixes #<issue number>
-->

<!--
Ensure each step in CONTRIBUTING.rst is complete, especially the following:

- Add tests that demonstrate the correct behavior of the change. Tests
  should fail without the change.
- Add or update relevant docs, in the docs folder and in code.
- Add an entry in CHANGES.rst summarizing the change and linking to the issue.
- Add `.. versionchanged::` entries in any relevant code docs.
-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
