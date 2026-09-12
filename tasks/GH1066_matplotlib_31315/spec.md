# GH1066_matplotlib_31315: [BUG] Warn when legend() receives mismatched handles and labels in 2-argument positional form — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/matplotlib/matplotlib/issues/24050
- Repo: https://github.com/matplotlib/matplotlib

## Issue Description

I had a bug in my code where I called `plot()` six times, stored the handles in a list, then called `legend()` with six handles, but seven labels for the legend.

It would have been very helpful if matplotlib raised an exception in this case.

`matplotlib.__version__` is 3.6.0, Python 3.9.6.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This seems like a pretty straightforward fix that could be a Good first issue for someone. It should be a matter of going into `_parse_legend_args` and verifying that the inputs are of a consistent length.

### Comment 2 ([user]):

may I try and fix this

### Comment 3 ([user]):

We don't assign issues; feel free to work on it.

### Comment 4 ([user]):

I would like to work on this!

### Comment 5 ([user]):

[user] there is already an open PR #24050. Please either add your suggestions as comment there, or choose another issue to work on.

### Comment 6 ([user]):

I changed this to medium difficulty because of some of the subtleties that came up in the discussion in #24061.

### Comment 7 ([user]):

> I changed this to medium difficulty because of some of the subtleties that came up in the discussion in #24061.

how to gauge depth of an issue from an noob standpoint?. I am asking because I raised a PR which was woefully shortsighted

### Comment 8 ([user]):

> how to gauge depth of an issue from an noob standpoint?

I think you can't. That's why we have the `Good first issue` and `Difficulty: ...` tags. If in doubt, feel fredd to ask. But as you can see, sometimes also the core devs don't oversee the difficulty.

## PR Review Comments

**[user]** on `lib/matplotlib/legend.py`:

Slightly more informative:
```suggestion
                f"Mismatched number of legend handles ({len(handles)}) and "
                f"labels ({len(labels)}). Truncating to the smaller number."
            )
```

**[user]** on `lib/matplotlib/tests/test_legend.py`:

```suggestion
    def test_legend_warns_on_unequal_number_of_handles_and_labels():
```
This name tells it all. We don't need to state github issues in code. - We could have added the warning right away when implementing `legend()` - that it was later added is an implementation detail. If the info is really needed, that can be extracted from the commit hash, which can be connected to the GH issue.

**[user]** on `lib/matplotlib/tests/test_legend.py`:

```suggestion
```

Not needed in tests, because cleanup is automatic.

**[user]** on `lib/matplotlib/tests/test_legend.py`:

Thank you for the suggestion — that is a much cleaner name.
Renaming to "test_legend_warns_on_unequal_number_of_handles_and_labels" as suggested. Agree that test names should be self-descriptive without referencing issue numbers.
I should also mention that this is my first contribution to matplotlib. I am likely unaware of several conventions and best practices followed in this codebase. I would genuinely appreciate any guidance or corrections — I am here to learn and will act on all feedback promptly.

**[user]** on `lib/matplotlib/tests/test_legend.py`:

This test class is for `fig.legend` not `ax.legend`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
