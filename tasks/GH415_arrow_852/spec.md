# GH415_arrow_852: Add case normalization to day of week parsing — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/arrow-py/arrow

## PR Description

## Pull Request Checklist

Thank you for taking the time to improve Arrow! Before submitting your pull request, please check all *appropriate* boxes:

<!-- Check boxes by placing an x in the brackets: [x] -->
- [x] 🧪 Added **tests** for changed code.
- [x] 🛠️ All tests **pass** when run locally (run `tox` or `make test` to find out!).
- [x] 🧹 All linting checks **pass** when run locally (run `tox -e lint` or `make lint` to find out!).
- [ ] 📚 Updated **documentation** for changed code.
- [x] ⏩ Code is **up-to-date** with the `master` branch.

If you have *any* questions about your code changes or any of the points above, please submit your questions along with the pull request and we will try our best to help!

## Description of Changes
Fixed a case sensitivity issue reported in #851, and added missing `asserts`!
Closes: https://github.com/arrow-py/arrow/issues/851
<!--
Replace this commented text block with a description of your code changes.

If your PR has an associated issue, insert the issue number (e.g. #703) or directly link to the GitHub issue (e.g. https://github.com/arrow-py/arrow/issues/703).

For example, doing the following will automatically close issue #703 when this PR is merged:

Closes: #703
-->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
