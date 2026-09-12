# GH1100_darts_2984: Fix/smape — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/unit8co/darts/issues/2983
- Repo: https://github.com/unit8co/darts

## Issue Description

**Describe the bug**
Calling smape where the actuals *and* predictions are zero at a point raises an error (incorrectly) claiming "`actual_series` must be strictly positive to compute the sMAPE."

**To Reproduce**
```
ts_actuals = TimeSeries.from_values(np.array([0, 2, 3, 4, 5])) 
ts_preds = (TimeSeries.from_values(np.array([0, 2, 3, 4, 5]) )) 

print(np.all(ts_actuals.values() == ts_preds.values()))  # True

smape(ts_actuals, ts_preds)  # Would expect 0.0, 40%, or raising ValueError depending on implementation
# ValueError: `actual_series` must be strictly positive to compute the sMAPE.
```

**Expected behavior**
I would expect that, as `smape` is defined for points of zero actual *or* prediction, it would evaluate to zero for points of exactly zero actual and exactly zero prediction, as it does not seem helpful or intuitive to raise an error in this very specific situation that represents a point of perfect prediction. 

eg, I would edit: 

```
    def sape(...)
    ... 
-    if not np.logical_or(y_true != 0, y_pred != 0).all():
-        raise_log(
-            ValueError(
-                "`actual_series` must be strictly positive to compute the sMAPE."
-            ),
-            logger=logger,
-        )
-    return 200.0 * np.abs(y_true - y_pred) / (np.abs(y_true) + np.abs(y_pred))

+   numerator = np.abs(y_true - y_pred) 
+   denominator = (np.abs(y_true) + np.abs(y_pred))
+   return 200 * np.where(denomenator == 0, 0.0, numerator / denominator)
```

Failing that, I would expect the error raised to correctly state that actuals and predictions must not *both* be zero. 

**System (please complete the following information):**
 - Python version: 3.10
 - darts version 0.40.0

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

Hi [user], thanks for reporting this and for the detailed suggestion!
I completely agree, the current error message is factually incorrect since we already allow zeros in the actual series as long as the forecast is non-zero. Furthermore, from a practical forecasting perspective, predicting 0 for an actual value of 0 should be treated as a perfect prediction (0.0 error) rather than a reason to crash a pipeline.
I'm in favor of removing the `ValueError` check and the strict positivity requirement entirely. Regarding the implementation, I’d suggest using `np.divide` with the `where` parameter rather than `np.where`. This avoids the `RuntimeWarning: invalid value encountered in divide` that occurs because `np.where` evaluates both branches before selecting the result.

The proposed change for the `sape` function would look like this:
```python
numerator = 200.0 * np.abs(y_true - y_pred)
denominator = np.abs(y_true) + np.abs(y_pred)

return np.divide(
    numerator, 
    denominator, 
    out=np.zeros_like(numerator, dtype=float), 
    where=denominator != 0
)
```

Would you like to submit a Pull Request with these changes (including a small update to the docstring and perhaps a test case for the (0,0) scenario)? Otherwise, I’m happy to implement it. Thanks again for helping improve Darts!

## PR Review Comments

**[user]** on `darts/metrics/metrics.py`:

```suggestion
        Optionally, whether to print operations progress.
```

**[user]** on `darts/metrics/metrics.py`:

```suggestion
```

**[user]** on `darts/metrics/metrics.py`:

```suggestion
   When :math:`\\left| y_t \\right| + \\left| \\hat{y}_t \\right| = 0` for some :math:`t` (i.e., both actual and 
   prediction are zero), the error for that time step is 0.
```

**[user]** on `darts/metrics/metrics.py`:

```suggestion
   When :math:`\\left| y_t \\right| + \\left| \\hat{y}_t \\right| = 0` for some :math:`t` (i.e., both actual and 
   prediction are zero), the error for that time step is 0.
```

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
