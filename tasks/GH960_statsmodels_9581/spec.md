# GH960_statsmodels_9581: BUG: make Binomial family more robust to corner case mu=0 , endog=0 — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/statsmodels/statsmodels/issues/9580
- Repo: https://github.com/statsmodels/statsmodels

## Issue Description

#### Description

The `loglike_obs` function in `genmod.families.family.Binomial` returns `nan` instead of `0` when `mu=0` and `endog=0`.   

One consequence of this is that a weighted logistic regression using GLM can return `nan` for the `llf` function, if there is an outlier observation that generates a very low probability.

This is related to (withheld: the upstream fix is not part of the task) , which fixes corner cases for `Binomial.loglike_obs`, but misses the case `mu=0, endog=0`.


#### Code samples
##### Direct call off `loglike_obs`
```python
from statsmodels.genmod.families.family import Binomial

# This should return 0, not nan
print(Binomial().loglike_obs(endog=0, mu=0))

# The symmetric case with endog=1, mu=1 properly returns 0
print(Binomial().loglike_obs(endog=1, mu=1))
```

##### Logistic regression example
```python
import pandas as pd
import statsmodels.api as sm

df = pd.DataFrame(dict(
    exog=[3,4,5,6,7,8,1000],  # The 1000 value produces a very low probability
    endog=[1,1,0,1,0,0,0],
    w=[1]*7
))

exog = sm.add_constant(df["exog"])
glm = sm.GLM(
    df.endog,
    exog,
    family=sm.families.Binomial(link=sm.genmod.families.links.Logit()),
)

fit = glm.fit()
# llf should not be nan
assert not pd.isna(fit.llf)
```

#### Expected Output

`Binomial().loglike_obs(endog=0, mu=0)` should return `0`.

Also, the `llf` in the above example should be approximately `-2.48` (the value obtained when the extreme value is omitted).


#### Output of ``import statsmodels.api as sm; sm.show_versions()``

<details>

[paste the output of ``import statsmodels.api as sm; sm.show_versions()`` here below this line]

INSTALLED VERSIONS
------------------
Python: 3.12.3.final.0
OS: Linux 6.8.0-60-generic #63-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 15 19:04:15 UTC 2025 x86_64
byteorder: little
LC_ALL: None
LANG: en_US.UTF-8

statsmodels
===========

Installed: 0.14.4

Required Dependencies
=====================

cython: Not installed
numpy: 2.3.0
scipy: 1.15.3
pandas: 2.3.0
    dateutil: 2.9.0.post0
patsy: 1.0.1

Optional Dependencies
...
pytest: Not installed
virtualenv: Not installed



</details>

## PR Review Comments

**[user]** on `statsmodels/genmod/families/family.py`:

## Alternative to the "Epsilon Trick"

Please consider this alternative approach instead of using the commonly applied *“epsilon trick”*:

```python
# Note that mu is still in (0, 1), i.e., not converted back

# y * log(mu) part
ll_y = np.where(np.isclose(y, 0), 0, y * np.log(mu))

# (n - y) * log(1 - mu) part
ll_ny = np.where(np.isclose(n, y), 0, (n - y) * np.log1p(-mu))

return (
    special.gammaln(n + 1) - special.gammaln(y + 1) -
    special.gammaln(n - y + 1) + ll_y + ll_ny
) * var_weights
```

🔍 What is log1p?

The function `np.log1p(x)` calculates the natural logarithm of 1 + x.

It offers much higher numerical precision than using `np.log(1 + x)` directly—especially when `x` is close to zero. This makes it especially useful in situations where precision is critical, such as probability computations.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
