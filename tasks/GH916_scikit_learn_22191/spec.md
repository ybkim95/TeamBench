# GH916_scikit_learn_22191: FIX poisson proxy_impurity_improvement — Full Specification (Planner Only)

## Source
- PR: (withheld: the upstream fix is not part of the task)
- Issue: https://github.com/scikit-learn/scikit-learn/issues/22186
- Repo: https://github.com/scikit-learn/scikit-learn

## Issue Description

### Describe the bug

[user]

[The Poisson objective](https://github.com/scikit-learn/scikit-learn/blob/ff09c8a579b116500deade618f93c4dc0d5750bd/sklearn/tree/_criterion.pyx#L1333) has a slight mistake in its derivation. 

Given an unregularised decision tree, as the depth increases we expect to see the training loss go to zero. This _does not_ occur in sklearn. We noticed this while implementing the same objective in the cuml project. 

The problem is that the loss of the left and right children get normalised by number of examples in each branch, such that they have equal weight even when the left child has many more examples that the right child.

This can be corrected by replacing this code: https://github.com/scikit-learn/scikit-learn/blob/ff09c8a579b116500deade618f93c4dc0d5750bd/sklearn/tree/_criterion.pyx#L1394

With something equivalent to this: https://github.com/rapidsai/cuml/blob/416ce61a478a879a49d685e9b06dc4e6d25cb758/cpp/src/decisiontree/batched-levelalgo/objectives.cuh#L316

## Issue Discussion (Root Cause Analysis)

### Comment 1 ([user]):

[user] Thanks for raising this issue. Do you have a minimal reproducible example where the described behaviour happens?
As we explicitly forbid splits that would produce a predicted value of `0` in a terminal node, your statement
> as the depth increases we expect to see the training loss go to zero

does not hold.

### Comment 2 ([user]):

We can illustrate the problem here, where the MSE objective converges faster than Poisson to Poisson training loss. This is corrected if the derivation is changed as suggested above.

<details>

```python
from sklearn.tree import DecisionTreeRegressor as sklDT
from sklearn.metrics import mean_poisson_deviance
import numpy as np
import pandas as pd
from scipy.stats import beta
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

matplotlib.use("Agg")
sns.set()


def beta_dataset():
    np.random.seed(33)
    n = 1000

    X = np.random.random((n, 4)).astype(np.float32)
    a, b = 2.31, 0.627
    y = beta.rvs(a, b, size=n).astype(np.float32) * 10
    return X, y


rs = np.random.RandomState(92)
depths = range(1, 8)
bootstrap = None
max_features = 1.0
n_estimators = 1
min_impurity_decrease = 0  # 1e-5
algo = {
    "skl_dt_poisson": sklDT(
        random_state=rs,
        min_impurity_decrease=min_impurity_decrease,
        criterion="poisson",
    ),
    "skl_dt_mse": sklDT(
        random_state=rs, min_impurity_decrease=min_impurity_decrease, criterion="mse",
    ),
}

datasets = {
    "poisson": beta_dataset(),
}
for data_name, (X, y) in datasets.items():
    X = X.astype(np.float32)
    y = y.astype(np.float32)
    df = pd.DataFrame(columns=["algorithm", "accuracy"])
    for d in depths:
        for name, alg in algo.items():
            name, alg, d
            alg.set_params(max_depth=d)
            alg.fit(X, y)

            pred = alg.predict(X)
            accuracy = mean_poisson_deviance(y, (pred))
            df = df.append(
                {"algorithm": name, "accuracy": accuracy, "depth": d},
                ignore_index=True,
            )

    print(df)
    sns.lineplot(data=df, x="depth", y="accuracy", hue="algorithm")
    plt.ylabel("train poisson")
    plt.tight_layout()
    plt.savefig("poisson_convergence.png")
    plt.clf()
```

</details>

![poisson_convergence](https://user-images.githubusercontent.com/7307640/148981066-d76dd66a-7ffc-462d-99de-bf63a1bb0c1e.png)

### Comment 3 ([user]):

You mean instead of
```python
proxy_impurity_left -= y_mean_left * log(y_mean_left)
proxy_impurity_right -= y_mean_right * log(y_mean_right)
```
it should be
```python
proxy_impurity_left -= self.sum_left[k] * log(y_mean_left)
proxy_impurity_right -= self.sum_right[k] * log(y_mean_right)
```
At first sight, I guess that's right and should be corrected.

## PR Review Comments

**[user]** on `sklearn/tree/_criterion.pyx`:

This is the fix.

**[user]** on `sklearn/ensemble/tests/test_forest.py`:

Debugging print that needs to be reverted?

**[user]** on `sklearn/tree/_criterion.pyx`:

With the removal of `1/n`, should we update the following?

https://github.com/scikit-learn/scikit-learn/blob/9816b35d05e139f1fcc1a5541a1398205280d75a/sklearn/tree/_criterion.pyx#L1347-L1350

It could be confusing to see the `n` being removed `proxy_impurity_improvement`'s docstring.

**[user]** on `sklearn/tree/_criterion.pyx`:

Nit:

```suggestion
            + sum_{i right}(y_i * log(y_i / y_pred_R))
```

**[user]** on `sklearn/tree/_criterion.pyx`:

I think and hope it is correct as it is. Mean Poisson loss is `1/n * sum_i ...` like MSE = `1 / n * sum_i ...`.

## Acceptance Criteria

1. All tests in the test suite pass: `pytest -x -q`
2. No regressions in unchanged functionality
3. Fix matches the approach described in the issue/PR discussion above

## Important Notes

- Only modify source files, not test files
- The test files already encode the correct expected behaviour
- Run `pytest -x -q` to verify your fix
