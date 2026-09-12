# GH371_arrow_1194: Update shift() for issue #1145 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/arrow-py/arrow

## PR Description

## Pull Request Checklist

Thank you for taking the time to improve Arrow! Before submitting your pull request, please check all *appropriate* boxes:

<!-- Check boxes by placing an x in the brackets like this: [x] -->
- [x] 🧪  Added **tests** for changed code.
- [x] 🛠️  All tests **pass** when run locally (run `tox` or `make test` to find out!).
- [x] 🧹  All linting checks **pass** when run locally (run `tox -e lint` or `make lint` to find out!).
- [x] 📚  Updated **documentation** for changed code.
- [x] ⏩  Code is **up-to-date** with the `master` branch.

If you have *any* questions about your code changes or any of the points above, please submit your questions along with the pull request and we will try our best to help!

## Description of Changes

Added check_imaginary parameter to the function referring to the issue #1145 
- New Parameter: Added a check_imaginary parameter (defaulting to True), which allows the user to decide whether or not to perform DST/imaginary time checks.
- Skip DST Check: The DST check logic:
block is only executed if check_imaginary is True. If set to False, this check is skipped for improved performance when DST changes are not a concern.

Benefits:
- Backward Compatibility: By default, the method still performs the DST/imaginary time checks, so existing code won't break.
- Performance Boost: Users who know that their datetime range does not involve DST transitions can set check_imaginary=False to skip the checks and improve performance.

## PR Review Comments

**[user]** on `arrow/arrow.py`:

Mind explaining why we want to force usage of check imaginary here rather than making it an argument?

**[user]** on `arrow/arrow.py`:

To bypass unnecessary checks when performance matters and they know they won't encounter DST transitions.

The default behavior of check_imaginary=True ensures that users get correct and valid results by default. If a user deliberately wants to skip the check for performance reasons or because they're confident it isn't needed, they can do so by setting the parameter to False.

**[user]** on `arrow/arrow.py`:

Ah my bad, I now see that this was added as true in range and dehumanize shift usages to maintain backwards compatibility right?

**[user]** on `arrow/arrow.py`:

Yes exactly

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
