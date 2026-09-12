# GH999_numpy_13813: BUG: further fixup to histogram2d dispatcher. — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/numpy/numpy

## PR Description

Now with tests....

Missed in #13757 - just goes to show that 3 pairs of eyes still isn't good enough, one needs to test, test, test! (Found during testing in astropy...)

## PR Review Comments

**[user]** on `numpy/lib/twodim_base.py`:

Let me suggest an alternative fix:
```python
    if N != 1 and N != 2:
        yield bins
    else:
        yield from bins  # bins=[x, y]
```

I like this better because the logic still matches up line for line with the function, which should make this easier to modify in the future.

**[user]** on `numpy/lib/tests/test_twodim_base.py`:

I'm not sure it's useful to return/check `args` and `kwargs` -- those are just directly passed on from the calling functions.

**[user]** on `numpy/lib/twodim_base.py`:

Looked at this again, and I think my implementation is right: for the `N=1` case we should just `yield bins` rather than `from bins`, since bins could very well just be a single integer (i.e., not iterable); only for a 2-element iterable does it contain separate items that could be overwritten).

**[user]** on `numpy/lib/tests/test_twodim_base.py`:

Yes, you're right, but it went in already....  And I guess it doesn't hurt to check.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
