# GH974_plotly.py_4922: fix: Skip base64 conversion for empty arrays (fixes #4919) — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/4919
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Our App Studio test suite caught an issue with this code in the latest RC of plotly.py:
```
df = pd.DataFrame({
  'x': [],
  'y': [],
})
fig = px.bar(df, x="x", y="y")
```

In v5.24.1, this produces an empty graph as expected
In v6.0.0rc0, this raises an Exception: `ValueError: zero-size array to reduction operation maximum which has no identity`

This is a simple case, but a more realistic use case would be when a dataframe is filtered down to nothing due to user input.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Thanks [user] for reporting, and for trying out the prerelease!

I've tried this out but can't reproduce the error:

![Image](https://github.com/user-attachments/assets/42095a62-9397-4eca-949b-a500e72a98f6)

Any chance you could share some more details please? Could you show the output of
```
import narwhals
narwhals.show_versions()
```
please?

### Comment 2 ([user]):

My apologies on the poor example code... must have been my EOD Friday brain 😅 

Here is code that DOES reproduce the error in a notebook. It's worth noting that the error occurs when `fig` is output (last line), and not when it is created.
```
df = pd.DataFrame({
  'x': ['a', 'b', 'c'],
  'y': [1 ,2, 3],
})
dff = df.query('x == "d"')
fig = px.bar(dff, x='x', y='y')
fig
```

![Image](https://github.com/user-attachments/assets/bea687d4-f2d2-43a5-8b91-b43b353b8f88)



And here is the same code as a Dash app, where the graph would be JSON-encoded rather than output directly. Here, the graph displays until you select `d` from the dropdown list. The error message comes from the callback (i.e. it's server-side) and is identical to the error produced in the notebook example.
```
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, callback, dcc, html

df = pd.DataFrame({
  'x': ['a', 'b', 'c'],
  'y': [1 ,2, 3],
})

app = Dash()
app.layout = [
  dcc.Dropdown(["a", "b", "c", "d"], value="a", id="inpt"),
  dcc.Graph(figure=px.bar(df, x='x', y='y'), id="outpt"),
]

@callback(
  Output("outpt", "figure"),
  Input("inpt", "value"),
  prevent_initial_call=True,
)
def cb(dropdown_selection):
  dff = df.query(f'x == "{dropdown_selection}"')
  return px.bar(dff, x='x', y='y')

server = app.server
if __name__ == "__main__":
  server.run(debug=True)

```

### Comment 3 ([user]):

Output from `narwhals.show_versions()`:

```
System:
    python: 3.12.7 (main, Nov 10 2011, 15:00:00) [GCC 14.2.0]
executable: ...
   machine: Linux-6.11.8-200.fc40.x86_64-x86_64-with-glibc2.40

Python dependencies:
     narwhals: 1.15.1
       pandas: 2.2.2
       polars: 1.14.0
         cudf: 
        modin: 0.32.0
      pyarrow: 17.0.0
        numpy: 1.26.4
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
