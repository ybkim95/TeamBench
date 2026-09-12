# GH1172_plotly.py_5000: fix: custom category order was hard-coded — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/4999
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Hey there, I've been having issues with the latest release, starting from v6.0.0, any pie plot made with plotly express raises a `polars.exceptions.ColumnNotFoundError` when passing the `category_orders `and `names` arguments at the same time.

A quick look at the traceback reveals a hardcoded column inside `process_dataframe_pie` function, which might be the source of the issue. I haven't tested this extensively and I don't know if it is by design or a bug.

In case anyone find themselves with this issue, for now I've found the following workarounds:
- Pin plotly to v5.24.1
- Sort the dataframe columns before passing it to `px.pie` and disable internal sorting with `fig.update_traces(sort=False)`
- Use `go.Pie` directly

**Error traceback**
```
2025-01-29 17:58:58.746 Uncaught app execution
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/site-packages/narwhals/_polars/dataframe.py", line 109, in func
    getattr(self._native_frame, attr)(*args, **kwargs)
  File "/usr/local/lib/python3.10/site-packages/polars/dataframe/frame.py", line 9586, in with_columns
    return self.lazy().with_columns(*exprs, **named_exprs).collect(_eager=True)
  File "/usr/local/lib/python3.10/site-packages/polars/lazyframe/frame.py", line 2056, in collect
    return wrap_df(ldf.collect(callback))
polars.exceptions.ColumnNotFoundError: b

Resolved plan until failure:

        ---> FAILED HERE RESOLVING 'with_columns' <---
DF ["status", "count"]; PROJECT */2 COLUMNS

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/components/statistics/home_graphs.py", line 121, in object_by_status_pie_plot
    pie_plot = px.pie(
  File "/usr/local/lib/python3.10/site-packages/plotly/express/_chart_types.py", line 1701, in pie
    return make_figure(
  File "/usr/local/lib/python3.10/site-packages/plotly/express/_core.py", line 2481, in make_figure
    args, trace_patch = process_dataframe_pie(args, trace_patch)
  File "/usr/local/lib/python3.10/site-packages/plotly/express/_core.py", line 2165, in process_dataframe_pie
    df.with_columns(
  File "/usr/local/lib/python3.10/site-packages/narwhals/dataframe.py", line 1764, in with_columns
    return super().with_columns(*exprs, **named_exprs)
  File "/usr/local/lib/python3.10/site-packages/narwhals/dataframe.py", line 138, in with_columns
    self._compliant_frame.with_columns(*compliant_exprs, **compliant_named_exprs),
  File "/usr/local/lib/python3.10/site-packages/narwhals/_polars/dataframe.py", line 113, in func
    raise ColumnNotFoundError(msg) from e
narwhals.exceptions.ColumnNotFoundError: b

Resolved plan until failure:

        ---> FAILED HERE RESOLVING 'with_columns' <---
DF ["status", "count"]; PROJECT */2 COLUMNS

Hint: Did you mean one of these columns: ['status', 'count']?
```

**Minimal example to reproduce this issue**

```python
import plotly.express as px
import polars as pl

df = pl.DataFrame({
    "status": ["On Route", "Pending", "Waiting Result", "Delivered"],
    "count": [28, 10, 73, 8]
})

custom_order = ["Pending", "Waiting Result", "On Route", "Delivered",]

fig = px.pie(
    data_frame=df,
    values="count",
    names="status",
    category_orders={"status": custom_order}, # raises polars.exceptions.ColumnNotFoundError
)

fig.show()
```

**Potential Source**
Hardcoded "b" column name on line 2166 of [packages/python/plotly/plotly/express/_core.py](https://github.com/plotly/plotly.py/blob/5e079e1119ee933645ec846689a4bc9d0cb41157/packages/python/plotly/plotly/express/_core.py#L2166)

```python
def process_dataframe_pie(args, trace_patch):
    names = args.get("names")
    if names is None:
        return args, trace_patch
    order_in = args["category_orders"].get(names, {}).copy()
    if not order_in:
        return args, trace_patch
    df: nw.DataFrame = args["data_frame"]
    trace_patch["sort"] = False
    trace_patch["direction"] = "clockwise"
    uniques = df.get_column(names).unique(maintain_order=True).to_list()
    order = [x for x in OrderedDict.fromkeys(list(order_in) + uniques) if x in uniques]

    # Sort args['data_frame'] by column 'b' according to order `order`.
    token = nw.generate_temporary_column_name(8, df.columns)
    args["data_frame"] = (
        df.with_columns(
            nw.col("b") # potential issue
            .replace_strict(order, range(len(order)), return_dtype=nw.UInt32)
            .alias(token)
        )
        .sort(token)
        .drop(token)
    )
    return args, trace_patch
```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks [user] for the report!

This might be due to 499e2facd5db337ca9fa9b95ac3951bc5cbe0d31 - [user] fancy taking a look? Should it be `names` instead of `nw.col('b')`?

EDIT in fact it looks like that commit was originally from (withheld: the upstream fix is not part of the task)files , so this is my bad here 😳 Will make a fix + test first thing in the morning

### Comment 2 ([user]):

Wow that was fast, thanks for the fix 😃

### Comment 3 ([user]):

Is there a workaround until this is published ? Besides ordering the original dataframe ?

## PR Review Comments

**[user]** on `packages/python/plotly/plotly/tests/test_optional/test_px/test_px_functions.py`:

I was doing a similar fix 🙈

You could also add the comparison with `go.Pie`:

```py
    values_ = np.array([
        x[0] for x in sorted(zip(data["count"], data["status"]), key=lambda t: custom_order.index(t[1]))
    ])
    trace = go.Pie(
        values=values_,
        labels=custom_order,
    )
    _compare_figures(trace, fig)
```

**[user]** on `packages/python/plotly/plotly/tests/test_optional/test_px/test_px_functions.py`:

yup, thanks for reviewing!

**[user]** on `packages/python/plotly/plotly/express/_core.py`:

[user] What's the reason for using `np.arange` here rather than `range`? Is there a performance difference?

**[user]** on `packages/python/plotly/plotly/express/_core.py`:

yes, [user] had noted that it was generally more performant, and numpy is still required in plotly express anyway - no objections to changing this back of course!

**[user]** on `packages/python/plotly/plotly/express/_core.py`:

Yup, makes sense to me, thanks!

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
