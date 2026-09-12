# GH1156_matplotlib_31031: RadioButtons: fix self._clicked method (followup to #30997) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/matplotlib/matplotlib

## PR Description

## PR summary

In #30997 the classes `RadioButtons` & `CheckButtons` started sharing more code, as they are fundamentally similar. When copy-pasting the methods that were seemingly identical, the `_clicked` method was copied from the original `CheckButtons` class, and there the `self._frames` object was used instead of `self._buttons`. This caused an error when actually using and clicking on buttons created with `RadioButtons`, as the `RadioButtons._frames` doesn't exist - something that unfortunately
the tests did not catch.

Both `CheckButtons._frames` and `CheckButtons._buttons` are very similar so even before #30997 the `CheckButtons._clicked` method could have used `self._checks` and not `self._frames`. Hence this change should be harmless.

## PR checklist

- [N/A] "closes #0000" is in the body of the PR description to [link the related issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- [x] new and changed code is [tested](https://matplotlib.org/devdocs/devel/testing.html)
- [N/A] *Plotting related* features are demonstrated in an [example](https://matplotlib.org/devdocs/devel/document.html#write-examples-and-tutorials)
- [N/A] *New Features* and *API Changes* are noted with a [directive and release note](https://matplotlib.org/devdocs/devel/api_changes.html#announce-changes-deprecations-and-new-features)
- [N/A] Documentation complies with [general](https://matplotlib.org/devdocs/devel/document.html#write-rest-pages) and [docstring](https://matplotlib.org/devdocs/devel/document.html#write-docstrings) guidelines

## PR Review Comments

**[user]** on `lib/matplotlib/tests/test_widgets.py`:

This should use the same form as e.g., `test_rectangle_selector` for events.

**[user]** on `lib/matplotlib/tests/test_widgets.py`:

Use the fixture for `ax`, as in other tests.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
