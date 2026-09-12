# GH940_great_expectati_8559: [BUGFIX] Use a randomized schema name when running snowflake tests to support concurrency — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

Tests running against a cloud-hosted DW have the potential for interfering with each-other as they are using a shared resource where entities may be created/dropped as part of a test. To avoid these race conditions, we use a randomized schema for each test.

- [x] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [x] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [x] Code is linted - run `invoke lint` (uses `black` + `ruff`)
- [x] Appropriate tests and docs have been updated

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
