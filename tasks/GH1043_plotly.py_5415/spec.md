# GH1043_plotly.py_5415: Fix bug where numpy datetime contained in Python list gets converted to integer — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/3957
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Dates specified using numpy `datetime64` with `[ns]` precision are handled incorrectly in plotting. Dates with microsec `[us]` precision or lower work as expected.
```
t0 = np.datetime64("2022-10-20T00:00:00").astype("datetime64[ns]")
t1 = np.datetime64("2022-10-21T00:00:00").astype("datetime64[ns]")

fig = go.Figure()
fig.add_trace(go.Scatter(x=[t0, t1], y=[3, 4], mode="lines"))
fig.show()
```
![newplot](https://user-images.githubusercontent.com/348089/202196194-068b9e15-080b-4135-9c98-612f8a954af9.png)

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

This is indeed a bug. However, a workaround would be to use `plotly.express` as the issue is not present there.

## PR Review Comments

**[user]** on `_plotly_utils/basevalidators.py`:

```suggestion
    Should only be used in contexts where we already know `np` is defined.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
