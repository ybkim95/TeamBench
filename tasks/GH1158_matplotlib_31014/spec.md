# GH1158_matplotlib_31014: TST: Fix warnings from Pillow for unavailable features — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/matplotlib/matplotlib

## PR Description

## PR summary

If Pillow is old enough to not support a feature _at all_, then it will warn about it (e.g., https://github.com/matplotlib/matplotlib/actions/runs/21232201791/job/61092807364#step:13:182). If you're running the whole test suite, then something else seems to cause pytest to treat it as benign. But if you run only `test_agg.py`, then our `-Werror` setting will cause it to fail test collection.

## PR checklist

- [n/a] "closes #0000" is in the body of the PR description to [link the related issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- [x] new and changed code is [tested](https://matplotlib.org/devdocs/devel/testing.html)
- [n/a] *Plotting related* features are demonstrated in an [example](https://matplotlib.org/devdocs/devel/document.html#write-examples-and-tutorials)
- [n/a] *New Features* and *API Changes* are noted with a [directive and release note](https://matplotlib.org/devdocs/devel/api_changes.html#announce-changes-deprecations-and-new-features)
- [n/a] Documentation complies with [general](https://matplotlib.org/devdocs/devel/document.html#write-rest-pages) and [docstring](https://matplotlib.org/devdocs/devel/document.html#write-docstrings) guidelines

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
