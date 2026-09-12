# GH897_sktime_8372: [BUG] Fix boundary equality in `EmpiricalCoverage` — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/8371
- Repo: https://github.com/sktime/sktime

## Issue Description

**Describe the bug**
The `EmpiricalCoverage` class incorrectly uses strict inequalities (`>` and `<`) instead of inclusive inequalities (`>=` and `<=`) when determining if true values fall within predicted confidence intervals. This leads to slight underestimation of empirical coverage by excluding boundary cases where true values exactly equal interval bounds.

**To Reproduce**
```python
import pandas as pd
from sktime.performance_metrics.forecasting.probabilistic import EmpiricalCoverage

y_true = pd.Series([2.0, 3.0, 4.0])
y_pred = pd.DataFrame(
    {
        ("var1", 0.8, "lower"): [1.0, 3.0, 3.0],  # Second true value equals lower bound
        ("var1", 0.8, "upper"): [3.0, 4.0, 5.0],
    }
)

metric = EmpiricalCoverage()
coverage = metric(y_true, y_pred)

# Should be 1.0 but returns less (0.66) due to strict inequalities
print(f"Current coverage: {coverage}")
```

**Expected behavior**
Empirical coverage should include boundary cases where true values exactly equal the lower or upper bounds of the prediction intervals. The mathematical definition of interval coverage is lower_bound ≤ y_true ≤ upper_bound, not lower_bound < y_true < upper_bound.

**Additional context**
The issue is in line 640 of `_classes.py`:
```python
truth_array = (y_true_np > lower).astype(int) * (y_true_np < upper).astype(int)
```
Should be:
```python
truth_array = (y_true_np >= lower).astype(int) * (y_true_np <= upper).astype(int)
```

**Versions**
<details>
System:
    python: 3.12.3 (main, Apr 15 2024, 18:07:06) [Clang 17.0.6 ]
executable: [/Users/marcrovira/Documents/repos/elux/zero-stockout/server/.venv/bin/python](https://file+.vscode-resource.vscode-cdn.net/Users/marcrovira/Documents/repos/elux/zero-stockout/server/.venv/bin/python)
   machine: macOS-15.3.2-x86_64-i386-64bit

Python dependencies:
          pip: None
       sktime: 0.37.0
      sklearn: 1.5.2
       skbase: 0.10.1
        numpy: 1.26.4
        scipy: 1.13.1
       pandas: 2.2.3
   matplotlib: 3.10.3
       joblib: 1.4.2
        numba: 0.61.2
  statsmodels: 0.14.4
     pmdarima: None
statsforecast: 2.0.1
      tsfresh: None
      tslearn: None
        torch: None
   tensorflow: None
</details>

Note: Issue created in part with LLM generated content, by Claude Sonnet 4.

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Good spot!

The same bug then must exist in `skpro` which we prepared for a merge down the line, so now there is duplicate code until that happens.

Would be much appreciated if you could open the same PR there:
https://github.com/sktime/skpro

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
