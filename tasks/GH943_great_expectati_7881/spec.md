# GH943_great_expectati_7881: [BUGFIX] Delete ExpectationSuite by name in GX Cloud — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/great-expectations/great_expectations

## PR Description

- Fix `CloudDataContextdelete_expectation_suite` to allow deleting ExpectationSuites by passing `expectation_suite_name`
- Update `GXCloudStoreBackend.remove_key` to support removal of `GXCloudIdentifier` keys with only `resource_name` attr defined

- [x] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [x] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB]
- [x] Code is linted

    ```
    black .

    ruff . --fix
    ```
- [x] Appropriate tests and docs have been updated

For more details, see our [Contribution Checklist](https://docs.greatexpectations.io/docs/contributing/contributing_checklist), [Coding style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/code_style), and [Documentation style guide](https://docs.greatexpectations.io/docs/contributing/style_guides/docs_style).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
