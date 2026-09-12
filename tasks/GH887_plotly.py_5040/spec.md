# GH887_plotly.py_5040: Fix TypeError: When using orjson and serializing pandas.NA — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/plotly/plotly.py/issues/5039
- Repo: https://github.com/plotly/plotly.py

## Issue Description

Reproduce the issue:

1. Install the orjson library.
2. Execute the following code:

```python
import pandas as pd
from plotly.io.json import to_json_plotly

to_json_plotly(pd.NA)
```

An error occurs when running the code:
```
Traceback (most recent call last):
  File "/opt/conda/envs/dev/lib/python3.10/site-packages/plotly/io/_json.py", line 171, in to_json_plotly
    return _safe(orjson.dumps(cleaned, option=opts).decode("utf8"), _swap_orjson)
TypeError: Type is not JSON serializable: NAType
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
