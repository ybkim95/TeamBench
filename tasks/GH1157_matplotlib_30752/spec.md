# GH1157_matplotlib_30752:  Improving error message for width and position type mismatch in violinplot — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: N/A
- Repo: https://github.com/matplotlib/matplotlib

## PR Description

This PR intends to close [ENH]: Support using datetimes as positions argument to violin(...) https://github.com/matplotlib/matplotlib/issues/30417

It should be possible to set the position of a violin plot to be a datetime. Currently, an attempt to do this results in this error message: TypeError: unsupported operand type(s) for +: 'float' and 'datetime.datetime'

The error stems from trying to perform operations between float and datetime if datetime was provided as position arguments.

The proposed solution improves the error message to be:

 "If positions are datetime/date values, pass widths as datetime.timedelta (e.g., datetime.timedelta(days=10)) or numpy.timedelta64.

unit tests are in tests\test_violinplot_datetime.py

I had opened another PR (withheld: the upstream fix is not part of the task), but messed up the commits while making changes. I am making this one after reading the suggestion here: (withheld: the upstream fix is not part of the task)#issuecomment-3262644574 by [user] . This change updates the error message instead of converting the position and width

## PR Review Comments

**[user]** on `lib/matplotlib/tests/test_axes.py`:

This PR handles date aspects on x-axis-related quantities. The stats refer to the y-axis and their unit does not matter in this PR. For simplicity and clarity, let's not use dates for them.

**[user]** on `lib/matplotlib/tests/test_axes.py`:

[user] 

 ```
 return [{
        'coords': datetimes,
        'vals': [0.1, 0.5, 0.2],
        'mean': datetimes[1],
        'median': datetimes[1],
        'min': datetimes[0],
        'max': datetimes[-1],
        'quantiles': datetimes
```

The quantities are the y-axis values- that, and the mean, median, min and max values for the quantities spread is what you are asking me to change? Just wanted to confirm

Something like this:

 ```
    'coords': datetimes,
        'vals': [0.1, 0.5, 0.2],
        'mean': 0.5,
        'median': 0.5,
        'min': 0.1,
        'max': 0.2,
        'quantiles': [0.1, 0.5, 0.2]
```

**[user]** on `lib/matplotlib/tests/test_axes.py`:

Yes, but please do not use obviously nonsensical data (like max < mean).

**[user]** on `lib/matplotlib/tests/test_axes.py`:

Please fix the statistics also here.

**[user]** on `lib/matplotlib/tests/test_axes.py`:

This test creates a figure but doesn't close it. While matplotlib typically handles this, it's better practice to either use a pytest fixture that manages figure lifecycle, or explicitly close the figure to avoid resource leaks in the test suite. Consider adding `plt.close(fig)` after the violin call or using a context manager.
```suggestion
    ax.violin(violin_plot_stats(), positions=positions, widths=widths)
    plt.close(fig)
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
