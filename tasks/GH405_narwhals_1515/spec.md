# GH405_narwhals_1515: fix: allow np.scalar to be used in Series.__getitem__ — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/narwhals-dev/narwhals/issues/1493
- Repo: https://github.com/narwhals-dev/narwhals

## Issue Description

The consequence of this is:
```python
In [18]: import pandas as pd

In [19]: import narwhals as nw

In [20]: s = pd.Series([0,1,2])

In [21]: snw = nw.from_native(s, series_only=True)

In [22]: snw[snw.min()]
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Cell In[22], line 1
----> 1 snw[snw.min()]

File ~/scratch/.venv/lib/python3.12/site-packages/narwhals/series.py:72, in Series.__getitem__(self, idx)
     70 if isinstance(idx, int):
     71     return self._compliant_series[idx]
---> 72 return self._from_compliant_series(self._compliant_series[idx])

File ~/scratch/.venv/lib/python3.12/site-packages/narwhals/_pandas_like/series.py:128, in PandasLikeSeries.__getitem__(self, idx)
    126 if isinstance(idx, int):
    127     return self._native_series.iloc[idx]
--> 128 return self._from_native_series(self._native_series.iloc[idx])

File ~/scratch/.venv/lib/python3.12/site-packages/narwhals/_pandas_like/series.py:139, in PandasLikeSeries._from_native_series(self, series)
    138 def _from_native_series(self, series: Any) -> Self:
--> 139     return self.__class__(
    140         series,
    141         implementation=self._implementation,
    142         backend_version=self._backend_version,
    143         dtypes=self._dtypes,
    144     )

File ~/scratch/.venv/lib/python3.12/site-packages/narwhals/_pandas_like/series.py:87, in PandasLikeSeries.__init__(self, native_series, implementation, backend_version, dtypes)
     79 def __init__(
     80     self,
     81     native_series: Any,
   (...)
     85     dtypes: DTypes,
     86 ) -> None:
---> 87     self._name = native_series.name
     88     self._native_series = native_series
     89     self._implementation = implementation

AttributeError: 'numpy.int64' object has no attribute 'name'
```

The place this needs changing is in the definition of `Series.__getitem__` for `_pandas_like`

## PR Review Comments

**[user]** on `narwhals/_pandas_like/series.py`:

Should this be a one liner to also check numpy is installed?

```suggestion
        if isisntance(idx, int) or ((np := get_numpy()) is not None and np.isscalar(idx)):
```

Edit: Nevermind, I guess pandas will keep depending on numpy forever anyway

**[user]** on `narwhals/_pandas_like/series.py`:

This is pandas-specific code, so isn't numpy guaranteed to be installed? Still, there's no harm checking.
You have a typo: could you please change `isisntance` to `isinstance`? Then I will commit your suggestion.
If you know of a more general way to check for scalars, that might be preferable.

**[user]** on `narwhals/_pandas_like/series.py`:

Yeah sorry, I realized that after the comment, apology for the inconvenience! I am resolving the comment

**[user]** on `narwhals/dependencies.py`:

is a NumPy Scalar, not NumPy Array

**[user]** on `tests/series_only/scalar_index_test.py`:

can we use `constructor_eager` here? like
````python
s = nw.from_native(constructor_eager({'a': [0,1,2]}), eager_only=True)['a']
assert s[s[0]] == 0
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
