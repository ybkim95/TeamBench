# GH913_sktime_3549: [BUG] Fix pipeline tag for NaN values — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/3547
- Repo: https://github.com/sktime/sktime

## Issue Description

**Describe the bug**

A forecasting pipeline that **contains an imputer** and a forecaster that **does not accept missing values** fails to work in the latest release of sktime (0.13.4). This used to work fine in 0.13.2 release.

**To Reproduce**

```python
# Works in 0.13.2, but fails in 0.13.4

import numpy as np
from sktime.datasets import load_longley
from sktime.forecasting.trend import TrendForecaster
from sktime.transformations.compose import TransformerPipeline
from sktime.forecasting.compose import ForecastingPipeline, TransformedTargetForecaster
from sktime.transformations.series.impute import Imputer

y, X = load_longley()
y[10] = np.nan  # Add missing values


transformer_y = TransformerPipeline(steps = [("imputer", Imputer())])

forecaster = TransformedTargetForecaster(
    steps = [
        ("transformer_y", transformer_y),
        ("model", TrendForecaster())
    ]
)

pipe = ForecastingPipeline(steps = [("forecaster", forecaster)])

pipe.fit(y)
```

```python-traceback
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
[<ipython-input-18-6f4acc86cd81>](https://localhost:8080/#) in <module>
----> 1 pipe.fit(y)

2 frames
[/usr/local/lib/python3.7/dist-packages/sktime/forecasting/base/_base.py](https://localhost:8080/#) in fit(self, y, X, fh)
    286 
    287         # check and convert X/y
--> 288         X_inner, y_inner = self._check_X_y(X=X, y=y)
    289 
    290         # set internal X/y to the new X/y

[/usr/local/lib/python3.7/dist-packages/sktime/forecasting/base/_base.py](https://localhost:8080/#) in _check_X_y(self, X, y)
   1298                 )
   1299 
-> 1300             _check_missing(y_metadata, "y")
   1301 
   1302         else:

[/usr/local/lib/python3.7/dist-packages/sktime/forecasting/base/_base.py](https://localhost:8080/#) in _check_missing(metadata, obj_name)
   1244                     )
   1245                 if metadata["has_nans"]:
-> 1246                     raise ValueError(msg)
   1247 
   1248         # retrieve supported mtypes

ValueError: ForecastingPipeline cannot handle missing data (nans), but y passed contained missing data.
```

**Expected behavior**
Would have expected this to work because there is an imputer in the pipeline.

**Additional context**
This used to work fine up until the 0.13.2 release. This started breaking after the recent 0.13.4 release (maybe even 0.13.3, but I have not explicitly tested that). **The initial impact was observed in pycaret when the unit tests started failing on GitHub.**

Working Notebook in 0.13.2: https://gist.github.com/ngupta23/fe385efcad52b1d6c4c11f955d13da8e
Notebook with error in 0.13.4: https://gist.github.com/ngupta23/c35b23ae7b786faff2f020a36efcbb38

**Versions**
<details>

<!--
Please run the following code snippet and paste the output here:
 
from sktime import show_versions; show_versions()
-->

</details>

<!-- Thanks for contributing! -->

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
