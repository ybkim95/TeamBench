# Reference solution — GH1125_featuretools_2254

> **GRADER-ONLY. DO NOT EXPOSE TO ANY AGENT ROLE.**
>
> This file holds the reference solution for `GH1125_featuretools_2254`. It was moved out of the
> agent-visible `spec.md` / `brief.md` by `scripts/deleak_specs.py` because
> the Planner could otherwise read the gold patch and the Executor could
> otherwise read the changed-file list, so neither role had to localize
> anything.
>
> `tasks/GH1125_featuretools_2254/reference/` must be excluded from every role's `allowed_roots`.
> It ships with the benchmark: the graders and the reference-solution
> admission gate need it.

## Moved from `spec.md`

## Files Changed in Fix

- `docs/source/release_notes.rst` (modified, +2/-1)
- `featuretools/primitives/standard/datetime_transform_primitives.py` (modified, +3/-16)
- `featuretools/primitives/utils.py` (modified, +27/-2)
- `featuretools/tests/primitive_tests/test_distancetoholiday_primitive.py` (modified, +3/-1)
- `featuretools/tests/requirement_files/latest_requirements.txt` (modified, +1/-1)

## Diff Summary (What the Fix Changes)

### `featuretools/primitives/standard/datetime_transform_primitives.py`
```diff
@@ -1,4 +1,3 @@
-import holidays
 import numpy as np
 import pandas as pd
 from woodwork.column_schema import ColumnSchema
@@ -991,24 +990,12 @@ class IsFederalHoliday(TransformPrimitive):
 
     def __init__(self, country="US"):
         self.country = country
-        try:
-            self.holidays = holidays.country_holidays(country=self.country)
-        except NotImplementedError:
-            available_countries = (
-                "https://github.com/dr-prodigy/python-holidays#available-countries"
-            )
-            error = "must be one of the available countries:\n%s" % available_countries
-            raise ValueError(error)
-        years_list = [1950 + x for x in range(150)]
-        self.federal_holidays = getattr(holidays, country)(years=years_list)
+        self.holidayUtil = HolidayUtil(country)
 
     def get_function(self):
         def is_federal_holiday(x):
-            holidays_df = pd.DataFrame(
-                sorted(self.federal_holidays.items()),
-                columns=["dates", "names"],
-            )
-            is_holiday = x.dt.normalize().isin(holidays_df.dates)
+            holidays_df = self.holidayUtil.to_df()
+            is_holiday = x.dt.normalize().isin(holidays_df.holiday_date)
             if x.isnull().values.any():
                 is_holiday = is_holiday.astype("object")
                 is_holiday[x.isnull()] = np.nan
```

### `featuretools/primitives/utils.py`
```diff
@@ -1,7 +1,7 @@
 import importlib.util
 import os
 from inspect import getfullargspec, getsource, isclass
-from typing import Dict, List
+from typing import Dict, List, Optional, Tuple
 
 import holidays
 import numpy as np
@@ -416,7 +416,11 @@ def _haversine_calculate(lat_1s, lon_1s, lat_2s, lon_2s, unit):
 class HolidayUtil:
     def __init__(self, country="US"):
         try:
-            holidays.country_holidays(country=country)
+            country, subdivision = self.convert_to_subdivision(country)
+            self.holidays = holidays.country_holidays(
+                country=country,
+                subdiv=subdivision,
+            )
         except NotImplementedError:
             available_countries = (
                 "https://github.com/dr-prodigy/python-holidays#available-countries"
@@ -433,3 +437,24 @@ def to_df(self):
         )
         holidays_df.holiday_date = holidays_df.holiday_date.astype("datetime64")
         return holidays_df
+
+    def convert_to_subdivision(self, country: str) -> Tuple[str, Optional[str]]:
+        """Convert country to country + subdivision
+
+           Created in response to library changes that changed countries to subdivisions
+
+        Args:
+            country (str): Original country name
+
+        Returns:
+            Tuple[str,Optional[str]]: country, subdivsion
+        """
+        return {
+            "ENGLAND": ("GB", country),
+            "NORTHERNIRELAND": ("GB", country),
+            "PORTUGALEXT": ("PT", "Ext"),
+            "PTE": ("PT", "Ext"),
+            "SCOTLAND": ("GB", country),
+            "UK": ("GB", country),
+            "WALES": ("GB", country),
+        }.get(country.upper(), (country, None))
```

## Moved from `brief.md`

        ## Files That May Need Changes

        - `featuretools/primitives/standard/datetime_transform_primitives.py`
- `featuretools/primitives/utils.py`
