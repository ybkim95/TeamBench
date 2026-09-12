# Reference solution — GH1133_darts_3015

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1133_darts_3015`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1133_darts_3015/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `CHANGELOG.md` (modified, +2/-0)
- `darts/dataprocessing/encoders/encoders.py` (modified, +26/-13)
- `darts/tests/utils/test_timeseries_generation.py` (modified, +9/-1)
- `darts/timeseries.py` (modified, +8/-4)
- `darts/utils/timeseries_generation.py` (modified, +9/-5)

## Diff Summary (What the Fix Changes)

### `darts/dataprocessing/encoders/encoders.py`
```diff
@@ -158,7 +158,7 @@
 
 import copy
 from collections.abc import Sequence
-from typing import Callable, Optional, Union
+from typing import Any, Callable, Optional, Union
 
 import numpy as np
 import pandas as pd
@@ -182,6 +182,7 @@
 from darts.utils.utils import generate_index
 
 SupportedTimeSeries = Union[TimeSeries, Sequence[TimeSeries]]
+
 logger = get_logger(__name__)
 
 ENCODER_KEYS = ["cyclic", "datetime_attribute", "position", "custom"]
@@ -203,7 +204,7 @@ def __init__(
         self,
         index_generator: CovariatesIndexGenerator,
         attribute: str,
-        tz: Optional[str] = None,
+        tz: Any = None,
     ):
         """
         Cyclic index encoding for `TimeSeries` that have a time index of type `pd.DatetimeIndex`.
@@ -221,7 +222,9 @@ def __init__(
             For more information, check out :meth:`datetime_attribute_timeseries()
             <darts.utils.timeseries_generation.datetime_attribute_timeseries>`
         tz
-            Optionally, a time zone to convert the time index to before computing the attributes.
+            Optionally, a time zone to convert the time index before computing attributes.
+            Supports any type handled by pandas
+            `tz_convert <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.tz_convert.html>`__.
         """
         super().__init__(index_generator)
         self.attribute = attribute
@@ -271,7 +274,7 @@ def __init__(
         input_chunk_length: Optional[int] = None,
         output_chunk_length: Optional[int] = None,
         lags_covariates: Optional[list[int]] = None,
-        tz: Optional[str] = None,
+        tz: Any = None,
     ):
         """
         Parameters
@@ -298,7 +301,9 @@ def __init__(
             Only required for :class:`SKLearnModel`.
             Corresponds to the lag values from parameter `lags_past_covariates` of :class:`SKLearnModel`.
         tz
-            Optionally, a time zone to convert the time index to before com
```

### `darts/timeseries.py`
```diff
@@ -3573,7 +3573,7 @@ def add_datetime_attribute(
         attribute,
         one_hot: bool = False,
         cyclic: bool = False,
-        tz: Optional[str] = None,
+        tz: Any = None,
     ) -> Self:
         """Return a new series with one (or more) additional component(s) that contain an attribute of the series' time
         index.
@@ -3600,7 +3600,9 @@ def add_datetime_attribute(
             Alternative to one_hot encoding, enable only one of the two.
             (adds 2 columns, corresponding to sin and cos transformation).
         tz
-            Optionally, a time zone to convert the time index to before computing the attributes.
+            Optionally, a time zone to convert the time index before computing attributes.
+            Supports any type handled by pandas
+            `tz_convert <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.tz_convert.html>`__.
 
         Returns
         -------
@@ -3625,7 +3627,7 @@ def add_holidays(
         country_code: str,
         prov: str = None,
         state: str = None,
-        tz: Optional[str] = None,
+        tz: Any = None,
     ) -> Self:
         """Return a new series with an added holiday component.
 
@@ -3644,7 +3646,9 @@ def add_holidays(
         state
             The state
         tz
-            Optionally, a time zone to convert the time index to before computing the attributes.
+            Optionally, a time zone to convert the time index before computing attributes.
+            Supports any type handled by pandas
+            `tz_convert <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.tz_convert.html>`__.
 
         Returns
         -------
```

### `darts/utils/timeseries_generation.py`
```diff
@@ -483,7 +483,7 @@ def holidays_timeseries(
     until: Optional[Union[int, str, pd.Timestamp]] = None,
     add_length: int = 0,
     dtype: np.dtype = np.float64,
-    tz: Optional[str] = None,
+    tz: Any = None,
 ) -> TimeSeries:
     """
     Creates a binary univariate TimeSeries with index `time_index` that equals 1 at every index that lies within
@@ -512,7 +512,9 @@ def holidays_timeseries(
     dtype
         The desired NumPy dtype (np.float32 or np.float64) for the resulting series.
     tz
-        Optionally, a time zone to convert the time index to before generating the holidays.
+        Optionally, a time zone to convert the time index before computing attributes.
+        Supports any type handled by pandas
+        `tz_convert <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.tz_convert.html>`__.
 
     Returns
     -------
@@ -549,7 +551,7 @@ def datetime_attribute_timeseries(
     add_length: int = 0,
     dtype=np.float64,
     with_columns: Optional[Union[list[str], str]] = None,
-    tz: Optional[str] = None,
+    tz: Any = None,
 ) -> TimeSeries:
     """
     Returns a new TimeSeries with index `time_index` and one or more dimensions containing
@@ -590,7 +592,9 @@ def datetime_attribute_timeseries(
         - If `one_hot` is ``True``, must be a list of strings of the same length as the generated one hot encoded
           features.
     tz
-        Optionally, a time zone to convert the time index to before computing the attributes.
+        Optionally, a time zone to convert the time index before computing attributes.
+        Supports any type handled by pandas
+        `tz_convert <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.tz_convert.html>`__.
 
     Returns
     -------
@@ -900,7 +904,7 @@ def _generate_new_dates(
 
 def _process_time_index(
     time_index: Union[TimeSeries, pd.DatetimeIndex],
-    tz: Optional[str] = None,
+    tz: Any = None,
     until: Optional[U
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `darts/dataprocessing/encoders/encoders.py`
- `darts/timeseries.py`
- `darts/utils/timeseries_generation.py`
