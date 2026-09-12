# GH518_narwhals_2280: fix: Expr.mode broadcasting — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/narwhals-dev/narwhals/issues/2273
- Repo: https://github.com/narwhals-dev/narwhals

## Issue Description

### Describe the bug

When applying expr.mode() on multiple columns (e.g. `df.select(nw.all().mode())`) and one returns one and another multiple values the output is incosistent. This is due to to an issue on the `polars` side of the operation. 

In `polars` this is dealt by using `df.select(nw.all().mode().first())` (https://docs.pola.rs/api/python/dev/reference/expressions/api/polars.Expr.mode.html).

### Steps or code to reproduce the bug

```python

import polars as pl
import pandas as pd
import narwhals as nw
from narwhals.typing import IntoFrame

data = {
    "a": [1, 1, 2, 2, 3],
    "b": [1, 2, 3, 3, 4],
}

df_pl = pl.DataFrame(data)
df_pd = pd.DataFrame(data)

def agnostic_mode(df_native: IntoFrame) -> IntoFrame:
    df = nw.from_native(df_native)
    return df.select(nw.all().mode())

agnostic_mode(df_pd)

agnostic_mode(df_pl)
```

### Expected results

```python
agnostic_mode(df_pd)
┌──────────────────┐
|Narwhals DataFrame|
|------------------|
|        a  b      |
|     0  1  3      |
|     1  2  3      |
└──────────────────┘

agnostic_mode(df_pl)
┌──────────────────┐
|Narwhals DataFrame|
|------------------|
|        a  b      |
|     0  1  3      |
|     1  2  3      |
└──────────────────┘
```

### Actual results

```python
agnostic_mode(df_pd)
┌──────────────────┐
|Narwhals DataFrame|
|------------------|
|        a  b      |
|     0  1  3      |
|     1  2  3      |
└──────────────────┘

agnostic_mode(df_pl)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/kstelios/Projects/narwhals-dev/narwhals/dataframe.py", line 1321, in select
    return super().select(*exprs, **named_exprs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/kstelios/Projects/narwhals-dev/narwhals/dataframe.py", line 180, in select
    self._compliant_frame.select(*compliant_exprs),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/kstelios/Projects/narwhals-dev/narwhals/_polars/dataframe.py", line 171, in func
    raise catch_polars_exception(e, self._backend_version) from None
narwhals.exceptions.ShapeError: Series b, length 1 doesn't match the DataFrame height of 2

If you want expression: col("b").mode() to be broadcasted, ensure it is a scalar (for instance by adding '.first()').
```

### Please run narwhals.show_version() and enter the output below.

```shell
System:
    python: 3.12.7 (main, Oct 16 2024, 04:37:19) [Clang 18.1.8 ]
executable: /home/kstelios/Projects/narwhals-dev/.venv/bin/python3
   machine: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.35

Python dependencies:
     narwhals: 1.31.0
       pandas: 2.2.3
       polars: 1.24.0
         cudf:
        modin: 0.32.0
      pyarrow: 19.0.1
        numpy: 2.2.3
```

### Relevant log output

```shell

```

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

thanks for the report

i'm really not sure what to do about `mode` tbh, I'm not sure I like it

I don't like how it's not an aggregation

I think it needs to be an aggregation, really. We could add a (required!, as this would be a break from the Polars API) argument `keep` to it, which could be:
- 'first'
- 'last'
- 'all': keep all values. Only supported for eager backends. This would not return an aggregation, so applying `nw.col('a', 'b').mode()` may raise `ShapeError` if 'a' and 'b' have a different number of modes. But, I think that's OK
- 'any'

'any' could be supported by all backends, the others only by eager ones

Then, `mode` would always return an aggregation, and this would solve a few problems

One annoyance is that there doesn't seem to be a groupby-mode function in pandas 😩 🤦  But, there is a nice workaround in https://github.com/pandas-dev/pandas/issues/19254 which we might be able to use?

## PR Review Comments

**[user]** on `narwhals/_arrow/series.py`:

definitely not the right solution

perhaps `_from_native_series` needs a "preserve_broadcast" boolean argument, which defaults to `False` but which we can selectively set to `True` for functions which we know don't change the length?

**[user]** on `narwhals/_arrow/series.py`:

[user] curious to hear your opinion on this if you have interest/time

**[user]** on `narwhals/_arrow/series.py`:

Thanks for the ping [user]!

I haven't taken a look at this yet, but did find the current `._broadcast` stuff a bit odd while working on `when-then-otherwise`.

`Dask` seems to have something that *looks* similar - but I didn't dig too deep into it

**[user]** on `narwhals/_arrow/series.py`:

Do you have info in `Expr._metadata` that would be useful to have passed down during `Expr.mode`?

**[user]** on `narwhals/_arrow/series.py`:

if we could make sure that compliant exprs are always have full `ExprMetadata` available, then maybe we wouldn't even need `_broadcast`

🤔 that should be feasible, and might be simpler

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
