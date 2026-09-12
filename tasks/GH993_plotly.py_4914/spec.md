# GH993_plotly.py_4914: fix: px.timeline was raising when x_start and/or x_end were already datetime for Polars / PyArrow — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/4913
- Repo: https://github.com/plotly/plotly.py

## Issue Description

If the user supplies a dataframe with correct dtypes (datetime), it will err as it's trying to cast them from string.

https://github.com/plotly/plotly.py/blob/master/packages/python/plotly/plotly/express/_core.py#L2125-L2129

It would be better if the casting is conditional, because right now I have to cast my datetime back to string, just for the function to cast it back to datetime.

plotly version 6.0.0rc1

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Wonderful, thanks [user] for trying out the prerelease, really appreciate it!

Indeed, here's reproducible example:
```python
import plotly.express as px
import polars as pl

data = {
    "Task": ["Research", "Design", "Implementation", "Testing", "Deployment"],
    "Start": ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-15", "2024-05-01"],
    "Finish": ["2024-01-31", "2024-02-28", "2024-04-14", "2024-04-30", "2024-05-15"],
    "Resource": ["Team A", "Team B", "Team A", "Team C", "Team B"]
}

df = pl.DataFrame(data).with_columns(pl.col('Start', 'Finish').str.to_date())

# Create the timeline
fig = px.timeline(
    df,
    x_start="Start",
    x_end="Finish",
    y="Task",
    color="Resource",
    title="Project Timeline",
    labels={"Resource": "Team Assigned"}
)

fig.update_yaxes(categoryorder="total ascending")  # Order tasks by start date
fig.show()
```
throws
```python-traceback
Traceback (most recent call last):
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/plotly/express/_core.py", line 2126, in process_dataframe_timeline
    df = df.with_columns(
         ^^^^^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/narwhals/dataframe.py", line 1402, in with_columns
    return super().with_columns(*exprs, **named_exprs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/narwhals/dataframe.py", line 118, in with_columns
    self._compliant_frame.with_columns(*exprs, **named_exprs),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/narwhals/_polars/dataframe.py", line 89, in func
    getattr(self._native_frame, attr)(*args, **kwargs)
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/polars/dataframe/frame.py", line 9211, in with_columns
    return self.lazy().with_columns(*exprs, **named_exprs).collect(_eager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/polars/lazyframe/frame.py", line 2029, in collect
    return wrap_df(ldf.collect(callback))
                   ^^^^^^^^^^^^^^^^^^^^^
polars.exceptions.SchemaError: invalid series dtype: expected `String`, got `date`

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/home/marcogorelli/scratch/t.py", line 14, in <module>
    fig = px.timeline(
          ^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/plotly/express/_chart_types.py", line 432, in timeline
    return make_figure(
           ^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/plotly/express/_core.py", line 2482, in make_figure
    args = process_dataframe_timeline(args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marcogorelli/scratch/.venv/lib/python3.12/site-packages/plotly/express/_core.py", line 2131, in process_dataframe_timeline
    raise TypeError(
TypeError: Both x_start and x_end must refer to data convertible to datetimes.
```

`.str.to_datetime` should only be called if Start / Finish aren't already of Datetime dtype

---

This only affects Polars plots, pandas ones are unaffected

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
