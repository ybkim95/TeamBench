# GH440_arrow_1228: Bump version to 1.4.0 and add changelog. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/arrow-py/arrow

## PR Description

## Pull Request Checklist

Thank you for taking the time to improve Arrow! Before submitting your pull request, please check all *appropriate* boxes:

<!-- Check boxes by placing an x in the brackets like this: [x] -->
- [ ] 🧪  Added **tests** for changed code.
- [ ] 🛠️  All tests **pass** when run locally (run `tox` or `make test` to find out!).
- [ ] 🧹  All linting checks **pass** when run locally (run `tox -e lint` or `make lint` to find out!).
- [ ] 📚  Updated **documentation** for changed code.
- [ ] ⏩  Code is **up-to-date** with the `master` branch.

If you have *any* questions about your code changes or any of the points above, please submit your questions along with the pull request and we will try our best to help!

## Description of Changes

<!--
Replace this commented text block with a description of your code changes.

If your PR has an associated issue, insert the issue number (e.g. #703) or directly link to the GitHub issue (e.g. https://github.com/arrow-py/arrow/issues/703).

Pro-tip: writing "Closes: #703" in the PR body will automatically close issue #703 when the PR is merged.
-->

## PR Review Comments

**[user]** on `CHANGELOG.rst`:

Can we update the date?

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
