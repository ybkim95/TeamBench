# GH973_sktime_4758: [BUG] allows probabilistic predictions in `DynamicFactor` in presence of exogenous variables — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/sktime/sktime/issues/4744
- Repo: https://github.com/sktime/sktime

## Issue Description

**Describe the bug**
<!--
A clear and concise description of what the bug is.
-->
`DynamicFactor` has `"ignores-exogeneous-X": False` and `"capability:pred_int": True`, but fails to predict quantiles when `X` is present.

**To Reproduce**
<!--
Add a Minimal, Complete, and Verifiable example (for more details, see e.g. https://stackoverflow.com/help/mcve

If the code is too long, feel free to put it in a public gist and link it in the issue: https://gist.github.com
-->

```python
from sktime.datasets import load_longley
_, df = load_longley()

y = df[["GNPDEFL", "GNP"]]
X = df[["UNEMP", "POP"]]

from sktime.forecasting.dynamic_factor import DynamicFactor
forecaster = DynamicFactor().fit(y[:10], X=X[:10])

forecaster.predict_quantiles(fh=[1, 2, 3, 4, 5, 6], X=X[10:])
```

**Expected behavior**
<!--
A clear and concise description of what you expected to happen.
-->
No error. Currently it fails with this:

> ValueError: Out-of-sample operations in a model with a regression component require additional exogenous values via the `exog` argument.

**Additional context**
<!--
Add any other context about the problem here.
-->
This is likely failing due to some issue in check of `exog`. Since `predict` works by checking on `self._forecaster`, failure in `_predict_interval` can be because of using `self._fitted_forecaster`.

**Versions**
<details>

<!--
Please run the following code snippet and paste the output here:

from sktime import show_versions; show_versions()
-->

```pycon
>>> from sktime import show_versions; show_versions()

System:
    python: 3.9.16 (main, Mar  8 2023, 14:00:05)  [GCC 11.2.0]
executable: /path/to/venv/bin/python
   machine: Linux-5.15.90.1-microsoft-standard-WSL2-x86_64-with-glibc2.35

Python dependencies:
          pip: 23.1.2
       sktime: 0.19.2
      sklearn: 1.2.2
       skbase: 0.4.0
        numpy: 1.24.3
        scipy: 1.10.1
       pandas: 1.5.3
   matplotlib: 3.7.1
       joblib: 1.2.0
  statsmodels: 0.13.5
        numba: 0.57.1
     pmdarima: 2.0.3
      tsfresh: 0.20.0
   tensorflow: 2.12.0
tensorflow_probability: 0.19.0
>>> 
```

</details>

<!-- Thanks for contributing! -->

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

hm, two questions without answer that I have while reading this:

* is this covered by the new functionality in the `_StatsModelsAdapter`, potentially related?
* why do the tests not detect this? They should, and they should test the proba predictions with exogeneous data.

### Comment 2 ([user]):

FYI [user]

### Comment 3 ([user]):

confirmed on current `main`, windows, python 3.10

### Comment 4 ([user]):

> * is this covered by the new functionality in the `_StatsModelsAdapter`, potentially related?

Related, but was not covered in that PR. We discuseed supporting multivariate models as well, but I skipped because of too much difference in handling prediction formats afterwards.

> * why do the tests not detect this? They should, and they should test the proba predictions with exogeneous data.

Not sure. I've added new tests now for both presence/absence of exogenous variables, and compare the predictions against `statsmodels` as well.

---

It's proabably completely out of scope because of the volume of work, but "human-readable summary of tests run for an estimator" is something that will help contributors (at least me) in long term. I should add that I've no idea if this is even possible to automate this or not, just said because I'm a bit confused on what all tests are exactly run for each estimator given too many tests/fixtures/conditions.

### Comment 5 ([user]):

> It's proabably completely out of scope because of the volume of work, but "human-readable summary of tests run for an estimator" is something that will help contributors (at least me) in long term. I should add that I've no idea if this is even possible to automate this or not, just said because I'm a bit confused on what all tests are exactly run for each estimator given too many tests/fixtures/conditions.

Have you tried out the return of `check_estimator`?

As a developer you can then search for each individual test in the repository, and that should have an informative docstring.

We could make this even nicer by giving `check_estimator` an optional return that has the test descriptions/docstrings, but I'd like to drill down what here is the main point of frustration for you.

### Comment 6 ([user]):

>> * is this covered by the new functionality in the `_StatsModelsAdapter`, potentially related?

>Related, but was not covered in that PR. We discuseed supporting multivariate models as well, but I skipped because of too much difference in handling prediction formats afterwards.

I see, so it's not covered by the adapter, makes sense.

>> * why do the tests not detect this? They should, and they should test the proba predictions with exogeneous data.

> Not sure. I've added new tests now for both presence/absence of exogenous variables, and compare the predictions against `statsmodels` as well.

I think the answer is from our discussion here: (withheld: the upstream fix is not part of the task)#issuecomment-1605781790

The proba methods are not tested with exogeneous data, and this is likely an oversight.

### Comment 7 ([user]):

> I'd like to drill down what here is the main point of frustration for you

[user] It's very much off the topic for this issue, and possibly not applicable to you/other developers/other users. I've created a discussion here to talk about this, to keep this issue for `DynamicFactor` only.

https://github.com/sktime/sktime/discussions/4762#discussion-5333940

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
